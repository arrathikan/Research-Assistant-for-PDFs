"""Liveness routes do not contact databases or external AI providers."""

from backend.gateway.schemas import HealthResponse, VersionedHealthResponse
from backend.shared.config import get_settings
from fastapi import APIRouter

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(environment=get_settings().app_env)


@router.get("/api/v1/health", response_model=VersionedHealthResponse)
async def api_v1_health() -> VersionedHealthResponse:
    return VersionedHealthResponse()
