"""Automated Tests for FastAPI Fundus Analysis Endpoints."""

import io
from pathlib import Path
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_fundus_status_endpoint():
    """Verify GET /api/fundus/status returns correct metadata and architecture."""
    response = client.get("/api/fundus/status")
    assert response.status_code == 200
    data = response.json()

    assert data["checkpoint_file"] == "best_model_v2.pth"
    assert "ResNet-18" in data["architecture"]
    assert "224x224" in data["input_resolution"]
    assert data["validation_metrics"]["fundus_image_auc"] == 0.727
    assert data["validation_metrics"]["cup_size_auc"] == 0.710
    assert data["validation_metrics"]["experimental_combined_auc"] == 0.755
    assert data["cd_ratio"]["status"] == "Not available from current fundus model"
    assert data["combined_score"]["status"] == "Unavailable until cup-size model is integrated"


def test_fundus_demo_cases_endpoint():
    """Verify GET /api/fundus/demo-cases returns available demonstration samples."""
    response = client.get("/api/fundus/demo-cases")
    assert response.status_code == 200
    cases = response.json()

    assert len(cases) >= 2
    assert any(c["id"] == "fundus_demo_glaucoma" for c in cases)
    assert any(c["id"] == "fundus_demo_normal" for c in cases)


def test_fundus_analyze_demo_case_glaucoma():
    """Verify POST /api/fundus/analyze with demo_case_id produces real inference and Grad-CAM."""
    response = client.post("/api/fundus/analyze", data={"demo_case_id": "fundus_demo_glaucoma"})
    assert response.status_code == 200
    data = response.json()

    assert data["is_valid"] is True
    assert data["status"] == "PASS"
    assert data["quality_status"] == "VALID"

    # Model Result
    m_res = data["model_result"]
    assert m_res["status"] == "TRAINED"
    assert m_res["checkpoint_file"] == "best_model_v2.pth"
    assert "glaucoma_probability" in m_res
    assert 0.0 <= m_res["glaucoma_probability"] <= 1.0
    assert m_res["predicted_class"] in (0, 1)
    assert m_res["validation_experiment_auc"] == 0.727

    # Explainability
    exp = data["explainability"]
    assert exp["available"] is True
    assert exp["gradient_l1_norm"] > 0.0
    assert exp["original_image"].startswith("data:image/png;base64,")
    assert exp["gradcam_heatmap"].startswith("data:image/png;base64,")
    assert exp["gradcam_overlay"].startswith("data:image/png;base64,")
    assert "do not independently establish a diagnosis" in exp["explanation_text"]

    # C/D Ratio and Combined Score Isolation
    assert data["cd_ratio"]["status"] == "UNAVAILABLE"
    assert data["cd_ratio"]["message"] == "Not available from current fundus model"
    assert data["combined_score"]["status"] == "UNAVAILABLE"
    assert "Unavailable until cup-size model is integrated" in data["combined_score"]["message"]


def test_fundus_analyze_uploaded_image():
    """Verify POST /api/fundus/analyze accepts multipart uploaded image files."""
    # Generate an in-memory valid test image
    img = Image.new("RGB", (300, 300), color=(180, 70, 30))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("test_patient_fundus.jpg", buf, "image/jpeg")}
    response = client.post(
        "/api/fundus/analyze",
        files=files,
        data={"patient_id": "PATIENT_FUNDUS_101", "eye": "OS"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["is_valid"] is True
    assert data["patient_context"]["patient_id"] == "PATIENT_FUNDUS_101"
    assert data["patient_context"]["eye"] == "OS"
    assert data["model_result"]["status"] == "TRAINED"
    assert data["explainability"]["available"] is True


def test_fundus_analyze_unsupported_file():
    """Verify POST /api/fundus/analyze gracefully rejects non-image inputs."""
    buf = io.BytesIO(b"random text data")
    files = {"file": ("corrupt_file.txt", buf, "text/plain")}
    response = client.post("/api/fundus/analyze", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["is_valid"] is False
    assert data["status"] == "FAIL"
    assert data["quality_status"] in ("wrong_modality", "unsupported_format", "WRONG_MODALITY")
