"""Unit tests for quiet doctor-facing clinical workstation endpoints."""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
from ml.preprocessing.oct_extractor_interface import StubOCTToRNFLTExtractor
from ml.models.staging_interface import StubGlaucomaStagingModel
from ml.forecasting.progression_forecaster import StubProgressionForecaster

client = TestClient(app)


def test_get_clinical_patients():
    """Verify GET /api/clinical/patients returns populated patient list."""
    response = client.get("/api/clinical/patients")
    assert response.status_code == 200
    patients = response.json()
    assert len(patients) >= 4
    assert any(p["id"] == "GM-DEMO-01" for p in patients)
    assert any(p["name"] == "Aarav Menon" for p in patients)


def test_direct_api_routes():
    """Verify direct REST routes: /api/patients, /api/scans, /api/reports, /api/visual-field."""
    r_pat = client.get("/api/patients")
    assert r_pat.status_code == 200
    assert len(r_pat.json()) >= 4

    r_scans = client.get("/api/scans")
    assert r_scans.status_code == 200
    assert len(r_scans.json()) >= 4

    r_rep = client.get("/api/reports")
    assert r_rep.status_code == 200
    assert len(r_rep.json()) >= 2

    r_vf = client.get("/api/visual-field")
    assert r_vf.status_code == 200
    assert len(r_vf.json()) >= 3


def test_get_patient_profile():
    """Verify GET /api/clinical/patients/{id} returns comprehensive clinical profile with timeline."""
    response = client.get("/api/clinical/patients/GM-DEMO-01")
    assert response.status_code == 200
    data = response.json()
    assert data["patient"]["name"] == "Aarav Menon"
    assert len(data["iop_records"]) >= 3
    assert len(data["visual_field_records"]) >= 3
    assert len(data["timeline"]) >= 3
    assert any(e["type"] == "IOP_MEASUREMENT" for e in data["timeline"])
    assert any(e["type"] == "VISUAL_FIELD" for e in data["timeline"])


def test_add_iop_measurement():
    """Verify POST /api/clinical/patients/{id}/iop records new measurement."""
    payload = {
        "patient_id": "GM-DEMO-01",
        "date": "2026-10-02",
        "eye": "OD",
        "iop_mmhg": 17.5,
        "method": "Goldmann Applanation",
        "notes": "Follow-up check.",
    }
    response = client.post("/api/clinical/patients/GM-DEMO-01/iop", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "SUCCESS"
    assert res["record"]["iop_mmhg"] == 17.5


def test_add_visual_field_measurement():
    """Verify POST /api/patients/{id}/visual-field records perimetric results."""
    payload = {
        "patient_id": "GM-DEMO-01",
        "date": "2026-10-02",
        "eye": "OD",
        "md_db": -6.1,
        "psd_db": 4.8,
        "vfi_pct": 89.0,
        "reliability": "Reliable",
        "notes": "Repeat test confirms superior nasal defect progression.",
    }
    response = client.post("/api/patients/GM-DEMO-01/visual-field", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "SUCCESS"
    assert res["record"]["md_db"] == -6.1


def test_add_clinical_report():
    """Verify POST /api/clinical/patients/{id}/reports attaches a clinical document."""
    payload = {
        "patient_id": "GM-DEMO-02",
        "report_date": "2026-10-02",
        "report_type": "Humphrey Visual Field 24-2",
        "eye": "OS",
        "notes": "Reliable test. All parameters normal.",
        "file_name": "HVF_24_2_Oct2026.pdf",
    }
    response = client.post("/api/clinical/patients/GM-DEMO-02/reports", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "SUCCESS"
    assert res["report"]["report_type"] == "Humphrey Visual Field 24-2"


def test_get_progression_assessment():
    """Verify progression rate calculation and data sufficiency handling."""
    # GM-DEMO-01 has 3 longitudinal RNFLT scans
    r1 = client.get("/api/patients/GM-DEMO-01/progression")
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["rnflt_progression"]["data_sufficient"] is True
    assert data1["rnflt_progression"]["estimated_slope_um_per_year"] is not None

    # GM-DEMO-05 has only 1 baseline scan -> data_sufficient must be False
    r5 = client.get("/api/patients/GM-DEMO-05/progression")
    assert r5.status_code == 200
    data5 = r5.json()
    assert data5["rnflt_progression"]["data_sufficient"] is False
    assert "More longitudinal measurements are required" in data5["rnflt_progression"]["message"]


def test_post_progression_forecast():
    """Verify POST /api/progression/forecast returns honest unavailable status without fake values."""
    payload = {
        "patient_id": "GM-DEMO-01",
        "horizons_months": [6, 12, 18, 24],
    }
    response = client.post("/api/progression/forecast", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["available"] is False
    assert res["status"] == "FORECAST_UNAVAILABLE"
    assert "24-month forecast unavailable" in res["message"]
    assert res["horizons"] == [6, 12, 18, 24]
    assert len(res["trajectory"]) == 0


def test_clinical_comparison():
    """Verify GET /api/patients/{id}/comparison returns pairwise scan metrics."""
    # GM-DEMO-01 has multiple scans
    res = client.get("/api/patients/GM-DEMO-01/comparison")
    assert res.status_code == 200
    data = res.json()
    assert data["comparison_available"] is True
    assert "latest_scan" in data
    assert "previous_scan" in data
    assert data["rnflt_difference_um"] is not None


def test_create_patient_with_photo():
    """Verify patient registration supports photo avatar and demo flag."""
    payload = {
        "name": "Dr. Maya Roy",
        "age": 59,
        "sex": "Female",
        "eye_laterality": "OU",
        "family_history": "Mother had bilateral glaucoma",
        "clinical_notes": "Referred for baseline RNFLT evaluation.",
        "photo_avatar": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "is_demo": False,
    }
    res = client.post("/api/patients", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Dr. Maya Roy"
    assert data["photo_avatar"].startswith("data:image/png;base64")
    assert data["is_demo"] is False


def test_ml_extensible_architecture_interfaces():
    """Verify extensibility interfaces for OCT extraction, staging, and forecasting."""
    extractor = StubOCTToRNFLTExtractor()
    assert extractor.is_validated is False
    ext_res = extractor.extract_rnflt_map(Path("test.png"))
    assert ext_res.success is False
    assert ext_res.status == "EXTRACTION_REQUIRED"

    staging = StubGlaucomaStagingModel()
    assert staging.is_validated is False
    stg_res = staging.evaluate_stage(None)
    assert stg_res.available is False
    assert stg_res.status == "STAGE_UNAVAILABLE"

    forecaster = StubProgressionForecaster()
    assert forecaster.is_validated is False
    fc_res = forecaster.forecast("test_patient", [], [], [])
    assert fc_res.available is False
    assert fc_res.status == "FORECAST_UNAVAILABLE"
