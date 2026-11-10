"""Gateway contracts and failure paths without external services."""

import json
import logging
from uuid import UUID

import pytest
from backend.gateway.main import app, create_app
from backend.gateway.schemas import HealthResponse, VersionedHealthResponse
from backend.shared.config import Settings
from backend.shared.logging import JsonFormatter
from backend.shared.models import ChatQueryRequest
from fastapi import Body, HTTPException
from fastapi.testclient import TestClient


def test_health_contracts():
    with TestClient(app) as client:
        HealthResponse.model_validate(client.get("/health").json())
        response = client.get("/api/v1/health")
        VersionedHealthResponse.model_validate(response.json())
        UUID(response.headers["X-Request-ID"])


@pytest.mark.parametrize(
    "origin,allowed", [("http://localhost:5173", True), ("https://untrusted.example", False)]
)
def test_cors(origin, allowed):
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
    assert (response.status_code == 200) is allowed
    assert (response.headers.get("access-control-allow-origin") == origin) is allowed


def test_environment_cors(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://research.example"]')
    assert Settings(_env_file=None).cors_origins == ["https://research.example"]


def test_not_found_and_method_errors():
    with TestClient(app) as client:
        assert client.get("/missing").json() == {"detail": "Not Found"}
        assert client.post("/api/v1/health").status_code == 405


def test_validation_and_unexpected_errors_do_not_leak():
    test_app = create_app()

    @test_app.post("/validate")
    async def validate(payload: ChatQueryRequest = Body()) -> dict:
        return payload.model_dump()

    @test_app.get("/crash")
    async def crash():
        raise RuntimeError("private-provider-key")

    @test_app.get("/unavailable")
    async def unavailable():
        raise HTTPException(503, "Service unavailable", headers={"Retry-After": "5"})

    with TestClient(test_app) as client:
        invalid = client.post("/validate", json={"message": "", "secret": "private"})
        assert invalid.status_code == 422
        assert invalid.json() == {"detail": "Invalid request"}
        crash_response = client.get("/crash")
        assert crash_response.status_code == 500
        assert crash_response.json() == {"detail": "Internal server error"}
        assert "X-Request-ID" in crash_response.headers
        unavailable_response = client.get("/unavailable")
        assert unavailable_response.status_code == 503
        assert unavailable_response.headers["Retry-After"] == "5"


def test_structured_logging():
    record = logging.LogRecord("gateway", logging.INFO, "", 0, "Request completed", (), None)
    record.request_id = "request-1"
    record.status_code = 200
    payload = json.loads(JsonFormatter().format(record))
    assert payload["request_id"] == "request-1"
    assert payload["status_code"] == 200
    assert payload["service"] == "gateway"
