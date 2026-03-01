from fastapi import status

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_get_projects_empty(client):
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert response.json() == []

def test_auth_authorized_with_mock(client):
    response = client.get("/api/expenses")
    # Should be 200 because auth is mocked in conftest.py
    assert response.status_code == 200
    assert isinstance(response.json(), list)
