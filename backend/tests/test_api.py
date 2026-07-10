import pytest
from app.models.auth_models import ApiKey
from app.models import Incident
import uuid

def test_health_check(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_readiness_check(client):
    response = client.get("/health/ready")
    # Our DB mock works, so readiness should pass
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

def test_create_incident(client):
    response = client.post("/api/v1/incidents/", json={
        "title": "Database connection spike",
        "description": "Saw 500 connections in 1 minute on primary DB",
        "service": "database-cluster",
        "severity": "CRITICAL"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Database connection spike"
    assert "INC-2026-" in data["id"]
    assert data["status"] == "TRIGGERED"

def test_get_incidents(client, db_session):
    # Seed DB
    inc = Incident(id="INC-TEST-01", title="Test Incident", service="web", severity="HIGH", status="TRIGGERED")
    db_session.add(inc)
    db_session.commit()

    response = client.get("/api/v1/incidents/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(i["id"] == "INC-TEST-01" for i in data)

def test_unauthorized_access(client):
    # Clear overrides to test missing auth
    client.app.dependency_overrides.clear()
    response = client.get("/api/v1/incidents/")
    assert response.status_code == 401
