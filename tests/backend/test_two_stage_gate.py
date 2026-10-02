"""Two-stage pipeline tests: MODE 1 RNFLT classifier vs MODE 2 raw OCT blocked; no false fallback."""
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_a_valid_rnflt_reaches_resnet():
    """MODE 1: genuine RNFLT map -> ResNet with full provenance, no QC bypass."""
    r = client.post("/api/analyze", data={"demo_case_id": "harvard_gd_test_0419"})
    assert r.status_code == 200
    d = r.json()
    assert d["is_valid"] is True
    assert d["input_type"] in ("rnflt_numeric", "rnflt_image")
    m = d["model_result"]
    assert m["status"] == "TRAINED"
    assert m["predicted_class"] in (0, 1)
    assert 0.0 <= m["model_estimated_classification_score"] <= 1.0
    assert m["debug"]["rnflt_source"] is not None
    assert m["debug"]["unit_validity"].startswith("µm genuine")
    assert d["explainability"]["available"] is True
    assert d["rnflt_analysis"]["dimensions"] == [225, 225]
    assert d["model_result"].get("prevented_false_result") is None


def test_b_raw_oct_cannot_reach_resnet_when_mgu_unavailable():
    """MODE 2: raw OCT B-scan blocked; rnflt_extraction.available false, model_result null."""
    r = client.post("/api/analyze", data={"demo_case_id": "demo_raw_oct_bscan"})
    assert r.status_code == 200
    d = r.json()
    assert d["is_valid"] is True
    assert d["input_type"] == "raw_oct"
    a = d["ai_analysis"]
    assert a["analysis_available"] is False
    assert a["rnflt_extraction"]["available"] is False
    assert "OCT segmentation checkpoint unavailable" in a["rnflt_extraction"]["reason"]
    assert a["prevented_false_result"] is True


def test_c_no_fallback_prediction_generated():
    """No zeros/random/demo fallback: logits/prob absent, no class."""
    r = client.post("/api/analyze", data={"demo_case_id": "demo_raw_oct_bscan"})
    d = r.json()
    assert d["model_result"] is None
    assert "rnflt_analysis" not in d
    assert d["explainability"]["available"] is False


def test_d_api_returns_model_result_null_for_raw_oct():
    """Raw OCT API contract: model_result exactly null, rnflt_extraction present."""
    r = client.post("/api/analyze", data={"demo_case_id": "demo_raw_oct_bscan"})
    d = r.json()
    assert d["model_result"] is None
    assert "rnflt_extraction" in d["ai_analysis"]
    assert d["ai_analysis"]["rnflt_extraction"]["available"] is False
    # input_type spelling consistent
    assert d["input_type"] == "raw_oct"


def test_e_ui_must_not_show_false_normal():
    """Ensure API does not return Normal/0% fields that UI could render as false result."""
    r = client.post("/api/analyze", data={"demo_case_id": "demo_raw_oct_bscan"})
    d = r.json()
    assert "predicted_class" not in (d.get("model_result") or {})
    assert "model_estimated_classification_score" not in (d.get("model_result") or {})
    assert d["ai_analysis"]["status"] == "RNFLT EXTRACTION REQUIRED"
    assert "Structural AI classification was not performed" in d["ai_analysis"]["message"]


def test_diagnostics_shows_two_stage_status():
    r = client.get("/api/model/diagnostics")
    assert r.status_code == 200
    j = r.json()
    ts = j.get("two_stage_architecture")
    assert ts is not None
    assert ts["sam2_base"] == "PASS"
    assert ts["mgu"] == "UNAVAILABLE"
    assert ts["rnflt_resnet"] == "PASS"
    assert "BLOCKED" in ts["end_to_end_raw_oct"]
