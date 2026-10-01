"""Comprehensive Master Pipeline Test Suite.
Verifies all 20 requirements specified in Master Product Specification Section 41:
1. Patient creation
2. Patient photo upload
3. OCT upload
4. OCT validation
5. RNFLT extraction interface
6. RNFLT validation
7. CNN inference
8. Grad-CAM
9. Save analysis
10. Add second scan
11. Longitudinal graph
12. IOP record
13. Visual field record
14. Report generation
15. PDF download
16. Print layout
17. Demo patient
18. Invalid OCT handling
19. Unsupported image handling
20. Missing extractor handling
"""

import io
import pytest
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app
from ml.preprocessing.oct_extractor_interface import (
    OCTToRNFLTExtractor,
    StubOCTToRNFLTExtractor,
    OCTModalityDetector,
    Modality,
    CalibratedRNFLTImageConverter,
)

client = TestClient(app)


# 1. Patient Creation
def test_master_01_patient_creation():
    payload = {
        "id": "PAT-TEST-001",
        "name": "David Miller",
        "dob": "1965-04-12",
        "age": 61,
        "sex": "Male",
        "eye": "OD",
        "family_history": "Maternal glaucoma",
        "notes": "Referred for baseline RNFL evaluation",
    }
    resp = client.post("/api/patients", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "PAT-TEST-001"
    assert data["name"] == "David Miller"
    assert data["age"] == 61


# 2. Patient Photo Upload
def test_master_02_patient_photo_upload():
    img_data = (np.random.RandomState(42).rand(64, 64, 3) * 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(img_data).save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("avatar.jpg", buf, "image/jpeg")}
    resp = client.post("/api/patients/PAT-TEST-001/photo", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "photo_url" in data
    assert data["photo_url"].startswith("/api/uploads/photos/")


# 3. OCT Scan Upload
def test_master_03_oct_scan_upload():
    img_data = (np.random.RandomState(42).rand(100, 100) * 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(img_data).save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("oct_scan_01.png", buf, "image/png")}
    data = {
        "patient_id": "PAT-TEST-001",
        "eye": "OD",
        "scan_date": "2026-09-01",
    }
    resp = client.post("/api/scans/upload", files=files, data=data)
    assert resp.status_code == 200
    res = resp.json()
    assert res["status"] in ["PASS", "VALID"]
    assert "scan_id" in res
    assert res["validation_stages"][0]["label"] == "Scan received"


# 4. OCT Validation Stages
def test_master_04_oct_validation_stages():
    # Valid study triggers all three stages
    resp = client.post("/api/analyze", data={"demo_case_id": "harvard_gd_test_0419"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    stages = [s["stage"] for s in data["validation_stages"]]
    assert "SCAN_RECEIVED" in stages
    assert "CHECKING_QUALITY" in stages
    assert "QUALITY_VERDICT" in stages
    assert data["quality_verdict"] == "Scan quality: Valid"


# 5. RNFLT Extraction Interface
def test_master_05_rnflt_extraction_interface():
    extractor = StubOCTToRNFLTExtractor()
    assert isinstance(extractor, OCTToRNFLTExtractor)
    assert extractor.extractor_name == "StubOCTToRNFLTExtractor (Interface Extension Point)"
    assert extractor.is_available is False

    res = extractor.extract("dummy_bscan.png", eye="OD")
    assert res.status == "EXTRACTION_REQUIRED"
    assert res.rnflt_map is None
    assert "RNFLT extraction is not currently available for this OCT study." in res.message


# 6. RNFLT Validation
def test_master_06_rnflt_validation():
    # Test valid 225x225 array
    valid_map = np.ones((225, 225), dtype=np.float32) * 80.0
    valid_map[10:50, 10:50] = 120.0
    assert CalibratedRNFLTImageConverter.validate_rnflt_array(valid_map) is True

    # Test corrupted dimensions
    invalid_dim = np.ones((20, 20), dtype=np.float32)
    assert CalibratedRNFLTImageConverter.validate_rnflt_array(invalid_dim) is False

    # Test NaN values
    nan_map = valid_map.copy()
    nan_map[0, 0] = np.nan
    assert CalibratedRNFLTImageConverter.validate_rnflt_array(nan_map) is False


# 7. Real CNN Inference
def test_master_07_cnn_inference():
    resp = client.post("/api/analyze", data={"demo_case_id": "harvard_gd_test_0419"})
    assert resp.status_code == 200
    m = resp.json()["model_result"]
    assert m["status"] == "TRAINED"
    assert m["checkpoint_file"] == "harvard_gd_rnflt_cnn_best.pt"
    assert 0.0 <= m["model_estimated_classification_score"] <= 1.0
    assert m["predicted_class"] in [0, 1]
    assert "AI Model Estimate" in m["wording_disclaimer"]
    assert "Clinical correlation required." in m["wording_disclaimer"]


# 8. Real Grad-CAM
def test_master_08_gradcam():
    resp = client.post("/api/analyze", data={"demo_case_id": "harvard_gd_test_0419"})
    assert resp.status_code == 200
    exp = resp.json()["explainability"]
    assert exp["available"] is True
    assert exp["gradients_verified_real"] is True
    assert exp["gradcam_overlay_image"].startswith("data:image/png;base64,")
    assert "Highlighted regions represent areas that influenced the model prediction" in exp["explanation_text"]


# 9. Save Analysis
def test_master_09_save_analysis():
    # Save a first scan to patient PAT-TEST-001
    resp = client.post("/api/analyze", data={
        "demo_case_id": "harvard_gd_test_0419",
        "patient_id": "PAT-TEST-001",
        "scan_date": "2026-09-01",
        "eye": "OD",
        "save_to_patient": True,
    })
    assert resp.status_code == 200
    
    # Check that scan exists in patient scan list
    scans_resp = client.get("/api/patients/PAT-TEST-001/scans")
    assert scans_resp.status_code == 200
    scans = scans_resp.json()
    assert len(scans) >= 1
    assert scans[0]["patient_id"] == "PAT-TEST-001"
    assert scans[0]["status"] == "Analyzed"


# 10. Add Second Scan (Repeated Follow-up)
def test_master_10_add_second_scan():
    resp = client.post("/api/analyze", data={
        "demo_case_id": "demo_glaucoma_0001",
        "patient_id": "PAT-TEST-001",
        "scan_date": "2026-10-01",
        "eye": "OD",
        "save_to_patient": True,
    })
    assert resp.status_code == 200

    scans_resp = client.get("/api/patients/PAT-TEST-001/scans")
    assert scans_resp.status_code == 200
    scans = scans_resp.json()
    assert len(scans) >= 2


# 11. Longitudinal Graph & Trends
def test_master_11_longitudinal_graph():
    resp = client.get("/api/patients/PAT-TEST-001/progression?eye=OD")
    assert resp.status_code == 200
    prog = resp.json()
    assert prog["patient_id"] == "PAT-TEST-001"
    assert len(prog["rnflt_trend"]) >= 2
    assert len(prog["score_trend"]) >= 2
    assert "observed_summary" in prog
    assert prog["observed_summary"]["total_scans"] >= 2
    assert "Observed structural trend" in prog["observed_summary"]["trend_description"]
    assert "24-month forecast unavailable" in prog["forecast"]["message"]


# 12. IOP Recording & History
def test_master_12_iop_recording():
    iop_payload = {
        "date": "2026-09-15",
        "eye": "OD",
        "iop_value": 21.5,
        "method": "Goldmann Applanation Tonometry",
        "notes": "Slightly elevated baseline IOP",
    }
    resp = client.post("/api/patients/PAT-TEST-001/iop", json=iop_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["measurement"]["iop_value"] == 21.5


# 13. Visual Field Recording & History
def test_master_13_visual_field_recording():
    vf_payload = {
        "date": "2026-09-20",
        "eye": "OD",
        "mean_deviation_db": -4.2,
        "pattern_standard_deviation_db": 3.8,
        "vfi_percent": 92.0,
        "test_type": "Humphrey 24-2 SITA-Standard",
        "notes": "Mild superior arcuate defect",
    }
    resp = client.post("/api/patients/PAT-TEST-001/visual-field", json=vf_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["measurement"]["mean_deviation_db"] == -4.2


# 14. Report Generation
def test_master_14_report_generation():
    resp = client.post("/api/patients/PAT-TEST-001/report/generate?eye=OD")
    assert resp.status_code == 200
    rep = resp.json()
    assert rep["patient_id"] == "PAT-TEST-001"
    assert "GLAUCOMAP" in rep["header"]["title"]
    assert "AI-generated research estimate — clinical correlation required." in rep["clinical_disclaimer"]
    assert rep["pdf_filename"].startswith("GlaucoMap_PAT-TEST-001_")


# 15. PDF Download
def test_master_15_pdf_download():
    # First generate report
    rep_resp = client.post("/api/patients/PAT-TEST-001/report/generate?eye=OD")
    assert rep_resp.status_code == 200
    rep_id = rep_resp.json()["id"]

    # Now download PDF
    pdf_resp = client.get(f"/api/reports/{rep_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in pdf_resp.headers["content-disposition"]
    # Check valid PDF header
    assert pdf_resp.content.startswith(b"%PDF")
    assert len(pdf_resp.content) > 1000


# 16. Print Layout & Report History
def test_master_16_print_layout_data():
    reports_resp = client.get("/api/patients/PAT-TEST-001/reports")
    assert reports_resp.status_code == 200
    reps = reports_resp.json()
    assert len(reps) >= 1
    assert "pdf_url" in reps[0]


# 17. Demo Patient (Aarav Menon)
def test_master_17_demo_patient():
    p_resp = client.get("/api/patients/GM-DEMO-01")
    assert p_resp.status_code == 200
    p = p_resp.json()
    assert p["name"] == "Aarav Menon"
    assert p["is_demo"] is True
    assert p["demo_disclaimer"] == "RESEARCH DEMO — NOT A REAL PATIENT"

    # Verify progression map has multiple serial scans
    prog_resp = client.get("/api/patients/GM-DEMO-01/progression?eye=OD")
    assert prog_resp.status_code == 200
    prog = prog_resp.json()
    assert len(prog["rnflt_trend"]) >= 3


# 18. Invalid OCT Handling (Zero Variance / Corrupt)
def test_master_18_invalid_oct_handling():
    # All zero blank image
    blank = np.zeros((100, 100), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(blank).save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("blank_scan.png", buf, "image/png")}
    resp = client.post("/api/analyze", files=files, data={"patient_id": "TEST_INVALID"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is False
    assert data["status"] == "FAIL"
    assert data["quality_verdict"] == "Scan quality: Unable to analyze"
    # CNN is NOT run
    assert "model_result" not in data or data.get("model_result", {}).get("status") in [None, "FAIL", "UNAVAILABLE"]


# 19. Unsupported Image Handling (.exe or invalid extension)
def test_master_19_unsupported_image_handling():
    buf = io.BytesIO(b"malicious content or plain text")
    files = {"file": ("test_study.exe", buf, "application/octet-stream")}
    resp = client.post("/api/analyze", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is False
    assert data["quality_status"] == "UNSUPPORTED_FORMAT"
    assert data["quality_verdict"] == "Scan quality: Unable to analyze"


# 20. Missing Extractor Handling for Raw OCT
def test_master_20_missing_extractor_handling():
    resp = client.post("/api/analyze", data={"demo_case_id": "demo_raw_oct_bscan"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["quality_verdict"] == "Scan quality: Valid"
    assert data["input_type"] == "raw_oct"
    assert data["ai_analysis"]["status"] == "RNFLT EXTRACTION REQUIRED"
    assert "RNFLT extraction is not currently available for this OCT study." in data["ai_analysis"]["message"]
    # CNN must be blocked
    assert data["model_result"]["status"] == "RNFLT_EXTRACTION_REQUIRED"
    assert "predicted_class" not in data["model_result"]
    assert data["explainability"]["available"] is False
