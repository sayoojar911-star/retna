"""Tests for OCT Analysis, Demo Cases, and Model Status Endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_get_demo_cases():
    """Verify demo cases endpoint returns verified local cases."""
    response = client.get("/api/v1/oct/demo-cases")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) >= 3
    assert any(c["id"] == "demo_normal_0002" for c in cases)
    assert any(c["id"] == "demo_glaucoma_0001" for c in cases)
    assert any(c["id"] == "demo_corrupt_invalid" for c in cases)


def test_model_status_endpoint():
    """Verify model status endpoint correctly reports training pending without fake metrics."""
    response = client.get("/api/v1/model/status")
    assert response.status_code == 200
    data = response.json()
    assert "pipeline" in data
    assert "hardware" in data
    assert "checkpoint" in data
    assert data["display_status"] in ("Development / Training Pending", "Trained Checkpoint Available")
    assert data["hardware"]["gpu_detected"] is True


def test_analyze_demo_normal_case():
    """Verify analysis of verified normal demo sample returns PASS and real statistics."""
    response = client.post("/api/v1/oct/analyze", data={"demo_case_id": "demo_normal_0002"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["status"] == "PASS"
    assert data["quality_status"] == "VALID"
    assert "rnflt_analysis" in data
    assert data["rnflt_analysis"]["mean_thickness_um"] > 0
    assert data["rnflt_analysis"]["heatmap_image"].startswith("data:image/png;base64,")
    assert data["model_status"]["checkpoint_status"] == "pending_training"


def test_analyze_demo_corrupt_case():
    """Verify quality control card catches and rejects corrupted input."""
    response = client.post("/api/v1/oct/analyze", data={"demo_case_id": "demo_corrupt_invalid"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert data["status"] == "FAIL"
    assert "Unable to process this OCT study" in data["message"]
    assert any(c["status"] == "FAIL" for c in data["validation_checks"])
