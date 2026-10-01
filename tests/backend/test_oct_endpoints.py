"""Tests for Real Harvard-GD CNN Inference, Real Grad-CAM, Demo Cases, and Model Status Endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_get_demo_cases():
    """Verify demo cases endpoint returns verified local cases including real Harvard-GD test samples."""
    response = client.get("/api/demo-cases")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) >= 5
    assert any(c["id"] == "harvard_gd_test_0419" for c in cases)
    assert any(c["id"] == "harvard_gd_test_0170" for c in cases)
    assert any(c["id"] == "demo_glaucoma_0001" for c in cases)
    assert any(c["id"] == "demo_normal_0002" for c in cases)
    assert any(c["id"] == "demo_corrupt_invalid" for c in cases)


def test_model_status_endpoint():
    """Verify model status endpoint correctly reports Harvard-GD CNN: TRAINED with real metrics."""
    response = client.get("/api/model/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "TRAINED"
    assert "Harvard-GD CNN: TRAINED" in data["display_status"]
    assert data["checkpoint"]["exists"] is True
    assert data["checkpoint"]["filename"] == "harvard_gd_rnflt_cnn_best.pt"
    assert data["metrics"] is not None
    assert "test_metrics" in data["metrics"]
    assert data["metrics"]["test_metrics"]["accuracy"] > 0.70


def test_analyze_real_harvard_gd_glaucoma_sample():
    """Verify analysis of real held-out Harvard-GD glaucoma sample (419) produces real CNN inference & Grad-CAM."""
    response = client.post("/api/analyze", data={"demo_case_id": "harvard_gd_test_0419"})
    assert response.status_code == 200
    data = response.json()

    # Technical Quality
    assert data["is_valid"] is True
    assert data["status"] == "PASS"
    assert data["quality_status"] == "VALID"

    # Quantitative RNFLT
    rnflt = data["rnflt_analysis"]
    assert rnflt["mean_thickness_um"] > 0
    assert rnflt["dimensions"] == [225, 225]
    assert rnflt["heatmap_image"].startswith("data:image/png;base64,")

    # Real Model Result
    m_res = data["model_result"]
    assert m_res["status"] == "TRAINED"
    assert m_res["checkpoint_file"] == "harvard_gd_rnflt_cnn_best.pt"
    assert m_res["predicted_class"] == 1
    assert m_res["predicted_category"] == "Glaucoma"
    assert 0.5 <= m_res["model_estimated_classification_score"] <= 1.0

    # Real Grad-CAM
    exp = data["explainability"]
    assert exp["available"] is True
    assert exp["gradients_verified_real"] is True
    assert exp["gradient_l1_norm"] > 0.0
    assert exp["original_rnflt_image"].startswith("data:image/png;base64,")
    assert exp["gradcam_heatmap_image"].startswith("data:image/png;base64,")
    assert exp["gradcam_overlay_image"].startswith("data:image/png;base64,")

    # Mandatory Medical Wording
    expected_disclaimer = "Highlighted regions represent areas that influenced the model prediction. They do not independently establish a diagnosis."
    assert exp["explanation_text"] == expected_disclaimer
    assert data["safety"]["explanation_disclaimer"] == expected_disclaimer
    assert "research-oriented decision-support prototype" in data["safety"]["clinical_prototype_notice"]


def test_analyze_real_harvard_gd_normal_control_sample():
    """Verify analysis of real held-out Harvard-GD normal sample (170) produces real predictions."""
    response = client.post("/api/analyze", data={"demo_case_id": "harvard_gd_test_0170"})
    assert response.status_code == 200
    data = response.json()

    assert data["is_valid"] is True
    assert data["status"] == "PASS"
    assert data["model_result"]["status"] == "TRAINED"
    assert data["explainability"]["available"] is True
    assert data["explainability"]["gradient_l1_norm"] > 0.0


def test_analyze_demo_corrupt_case():
    """Verify quality control card catches and rejects corrupted input without stack traces."""
    response = client.post("/api/analyze", data={"demo_case_id": "demo_corrupt_invalid"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert data["status"] == "FAIL"
    assert "Unable to process this OCT study" in data["message"]
    assert any(c["status"] == "FAIL" for c in data["validation_checks"])


def test_analyze_missing_input():
    """Verify missing input handling returns clean user-facing error."""
    response = client.post("/api/analyze")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert data["status"] == "FAIL"
    assert data["quality_status"] == "MISSING_INPUT"


def test_analyze_raw_oct_bscan_study():
    """Verify raw OCT study passes technical validation but is strictly prevented from entering the RNFLT CNN."""
    response = client.post("/api/analyze", data={"demo_case_id": "demo_raw_oct_bscan"})
    assert response.status_code == 200
    data = response.json()

    # 1. Image loads and technical validation passes
    assert data["is_valid"] is True
    assert data["status"] == "PASS"
    assert data["input_type"] == "raw_oct"
    assert "Raw OCT study imported successfully" in data["message"]

    # 2. Dimensions are detected
    raw_study = data.get("raw_oct_study")
    assert raw_study is not None
    assert raw_study["technical_validation"] == "PASS"
    assert raw_study["input_integrity"] == "PASS"
    assert raw_study["dimensions"] == [400, 512]
    assert raw_study["preview_image"].startswith("data:image/png;base64,")

    # 3. AI Analysis status is RNFLT EXTRACTION REQUIRED
    ai_analysis = data.get("ai_analysis")
    assert ai_analysis is not None
    assert ai_analysis["status"] == "RNFLT EXTRACTION REQUIRED"
    assert ai_analysis["analysis_available"] is False
    assert "The current trained model operates on numerical RNFLT maps" in ai_analysis["message"]
    assert "OCT-to-RNFLT extraction/segmentation" in ai_analysis["message"]

    # 4. Strict check: NO prediction or confidence score or Grad-CAM
    assert "rnflt_analysis" not in data
    assert data["model_result"]["status"] == "RNFLT_EXTRACTION_REQUIRED"
    assert "model_estimated_classification_score" not in data["model_result"]
    assert "predicted_class" not in data["model_result"]
    assert data["explainability"]["available"] is False
    assert "gradcam_heatmap_image" not in data["explainability"]


def test_upload_raw_oct_png_blocks_cnn(tmp_path):
    """Verify an uploaded raw OCT PNG is validated and prevented from running through the RNFLT CNN."""
    import io
    from PIL import Image
    import numpy as np

    # Generate a realistic non-zero variance synthetic B-scan image
    img_data = (np.random.RandomState(42).rand(200, 300) * 255).astype(np.uint8)
    img = Image.fromarray(img_data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("test_study.png", buf, "image/png")}
    response = client.post("/api/analyze", files=files, data={"patient_id": "TEST_RAW_01"})
    assert response.status_code == 200
    data = response.json()

    assert data["is_valid"] is True
    assert data["input_type"] == "raw_oct"
    assert data["raw_oct_study"]["dimensions"] == [200, 300]
    assert data["ai_analysis"]["status"] == "RNFLT EXTRACTION REQUIRED"
    assert data["model_result"]["status"] == "RNFLT_EXTRACTION_REQUIRED"
    assert "model_estimated_classification_score" not in data["model_result"]
    assert data["explainability"]["available"] is False
