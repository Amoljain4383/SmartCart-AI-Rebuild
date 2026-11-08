"""Tests for API health and root metadata endpoints."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_status():
    """Verify root endpoint returns demo mode disclaimer and integer paise currency unit."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["currency"] == "INR"
    assert "Integer Paise" in data["monetary_unit"]
    assert data["demo_mode"] is True
    assert "simulated demo data" in data["notice"].lower()


def test_health_check():
    """Verify database connectivity via /health."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
