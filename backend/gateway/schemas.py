"""Public gateway contracts; health reports process liveness only."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["healthy"] = "healthy"
    service: Literal["gateway"] = "gateway"
    environment: str
    version: str = "0.1.0"


class VersionedHealthResponse(BaseModel):
    status: Literal["healthy"] = "healthy"
    service: Literal["gateway"] = "gateway"
    api_version: Literal["v1"] = "v1"


class ErrorResponse(BaseModel):
    detail: str
