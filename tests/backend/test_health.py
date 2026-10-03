def test_health_endpoint_status_code(client):
    """Verify that GET /health returns HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_payload(client):
    """Verify that GET /health returns correct status and service name."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "glaucomap-backend"


def test_api_v1_health_endpoint(client):
    """Verify that GET /api/v1/health also returns valid health payload."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "glaucomap-backend"
