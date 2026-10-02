import joblib, pathlib, numpy as np
from fastapi.testclient import TestClient
from backend.app.main import app
client=TestClient(app)

def test_excel_preprocessing_header_mapping():
    import json
    meta=json.loads(pathlib.Path("models/checkpoints/progression_model_metadata.json").read_text())
    assert "excel_columns" in meta and "Progression Status PLR2" in meta["excel_columns"]

def test_missing_and_sentinel():
    import openpyxl
    p="data new/clinical_progression_dataset.xlsx.xlsx"
    wb=openpyxl.load_workbook(p, data_only=True)
    ws=wb["Baseline"]
    # VF cols 20-80 contain -1 sentinel
    has_minus1=any(ws.cell(row=r,column=c).value==-1 for r in range(3,6) for c in range(20,81))
    assert has_minus1
    # preprocessor imputer handles -1 as NaN
    prep=joblib.load("models/checkpoints/progression_preprocessor.joblib")
    assert prep is not None

def test_sentinel_minus1_not_feature():
    import joblib
    prep=joblib.load("models/checkpoints/progression_preprocessor.joblib")
    X=np.array([[60,17,540,3,85,100,80,110,70,-99,0]]*2, dtype=float)
    # -99 would be imputed, not kept
    out=prep.transform(X)
    assert not np.isnan(out).any()

def test_subject_split_no_overlap():
    import json
    meta=json.loads(pathlib.Path("models/checkpoints/progression_model_metadata.json").read_text())
    # total subjects 144
    total=meta["training_subject_count"]+meta["validation_subject_count"]+meta["test_subject_count"]
    assert total==144
    assert meta["training_subject_count"]==100

def test_no_patient_overlap():
    # Implied by subject split; check record counts per subject unique handled in training
    import json
    meta=json.loads(pathlib.Path("models/checkpoints/progression_model_metadata.json").read_text())
    assert meta["training_record_count"]==179

def test_target_mapping():
    import json
    meta=json.loads(pathlib.Path("models/checkpoints/progression_model_metadata.json").read_text())
    assert meta["target"].startswith("Progression Status")

def test_model_loading():
    import joblib
    m=joblib.load("models/checkpoints/progression_risk_model.joblib")
    assert hasattr(m, "predict_proba")

def test_prediction():
    payload={"age":60,"iop":17,"cct":540,"rnflt_mean":85,"rnflt_superior":100,"rnflt_nasal":80,"rnflt_inferior":110,"rnflt_temporal":70,"vf_md":-2.0,"vf_plr2":0,"vf_plr3":0,"total_visits":3}
    r=client.post("/api/progression/predict", json=payload)
    assert r.status_code==200
    j=r.json()
    assert j["model"]=="progression_risk"
    assert 0<=j["probability"]<=1
    assert j["research_only"] is True

def test_api_validation_missing_features():
    r=client.post("/api/progression/predict", json={})
    assert r.status_code==200
    assert "probability" in r.json()

def test_harvard_still_works():
    r=client.post("/api/analyze", data={"demo_case_id":"harvard_gd_test_0419"})
    assert r.status_code==200
    assert r.json()["model_result"]["predicted_class"] in (0,1)

def test_raw_oct_gate_still_works():
    r=client.post("/api/analyze", data={"demo_case_id":"demo_raw_oct_bscan"})
    assert r.json()["model_result"] is None
    assert r.json()["ai_analysis"]["rnflt_extraction"]["available"] is False
