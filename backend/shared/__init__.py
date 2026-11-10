"""Shared configuration, data models, and logging for ResearchAI backend microservices."""

from backend.shared.config import Settings, get_settings
from backend.shared.models import (
    DocumentStatus,
    DocumentMetadata,
    ChunkMetadata,
    StructuredSummary,
    CitationReference,
    ChatQueryRequest,
    ChatQueryResponse,
)

__all__ = [
    "Settings",
    "get_settings",
    "DocumentStatus",
    "DocumentMetadata",
    "ChunkMetadata",
    "StructuredSummary",
    "CitationReference",
    "ChatQueryRequest",
    "ChatQueryResponse",
]
