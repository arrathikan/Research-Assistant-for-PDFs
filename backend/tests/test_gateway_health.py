"""Tests for FastAPI Gateway health endpoints."""

from fastapi.testclient import TestClient
from backend.gateway.main import app

client = TestClient(app)


def test_system_health():
    """Verify /health endpoint returns healthy status and service name."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "gateway"
    assert "version" in data


def test_api_v1_health():
    """Verify /api/v1/health endpoint returns api_version."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["api_version"] == "v1"
