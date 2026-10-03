from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def _patient_id() -> str:
    r = client.post("/api/patients", json={"name": "Phase2 Patient", "age": 60, "sex": "Female", "eye": "OD"})
    assert r.status_code in (200, 201)
    j = r.json()
    return j.get("id") or j.get("patient_id")


def test_patient_creation():
    r = client.post("/api/patients", json={"name": "T Patient", "age": 55, "sex": "Male", "eye": "OS", "dob": "1970-01-01"})
    assert r.status_code in (200, 201)
    data = r.json()
    assert (data.get("name") == "T Patient")


def test_visit_creation():
    pid = _patient_id()
    r = client.post(f"/api/patients/{pid}/visits", json={"visit_date": "2026-10-01", "eye": "OD", "qc_status": "VALID", "mean_rnflt_um": 82.0, "iop_mmhg": 16, "vf_md_db": -1.2})
    assert r.status_code == 200, r.text
    assert r.json()["visit"]["visit_date"] == "2026-10-01"
    assert r.json()["visit"]["eye"] == "OD"


def test_multiple_visits_preserved():
    pid = _patient_id()
    for d, rnfl in [("2026-10-01", 88.0), ("2026-10-15", 86.5), ("2026-11-01", 84.1)]:
        r = client.post(f"/api/patients/{pid}/visits", json={"visit_date": d, "eye": "OD", "mean_rnflt_um": rnfl})
        assert r.status_code == 200
    r = client.get(f"/api/patients/{pid}/visits")
    assert r.status_code == 200
    visits = r.json()
    assert len(visits) == 3
    assert [v["mean_rnflt_um"] for v in visits] == [88.0, 86.5, 84.1]


def test_retrieving_history_sorted():
    pid = _patient_id()
    client.post(f"/api/patients/{pid}/visits", json={"visit_date": "2026-11-02", "eye": "OD"})
    client.post(f"/api/patients/{pid}/visits", json={"visit_date": "2026-10-02", "eye": "OD"})
    r = client.get(f"/api/patients/{pid}/visits")
    assert [v["visit_date"] for v in r.json()] == sorted([v["visit_date"] for v in r.json()])


def test_invalid_visit_rejected():
    pid = _patient_id()
    r = client.post(f"/api/patients/{pid}/visits", json={"visit_date": "", "eye": "OD"})
    assert r.status_code in (400, 422)
    r2 = client.post(f"/api/patients/{pid}/visits", json={"visit_date": "2026-10-01", "eye": ""})
    assert r2.status_code in (400, 422)


def test_visit_never_overwrites_previous_and_persists_analysis_fields():
    pid = _patient_id()
    r1 = client.post(f"/api/patients/{pid}/visits", json={"visit_date": "2026-10-01", "eye": "OD", "mean_rnflt_um": 90.0, "model_version": "harvard_gd_rnflt_cnn_best.pt", "predicted_class": 0})
    assert r1.status_code == 200
    r2 = client.post(f"/api/patients/{pid}/visits", json={"visit_date": "2026-10-15", "eye": "OD", "mean_rnflt_um": 88.0, "predicted_class": 1})
    assert r2.status_code == 200
    visits = client.get(f"/api/patients/{pid}/visits").json()
    assert visits[0]["predicted_class"] == 0
    assert visits[1]["predicted_class"] == 1
    assert visits[0]["mean_rnflt_um"] == 90.0
