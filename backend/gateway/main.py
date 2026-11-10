"""API Gateway entrypoint for ResearchAI.

Exposes REST endpoints for PDF uploading, document status tracking,
structured summary retrieval, and conversational Hybrid RAG queries.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.shared.config import get_settings
from backend.shared.logging import setup_logger

settings = get_settings()
logger = setup_logger("gateway", settings.log_level)

app = FastAPI(
    title="ResearchAI Gateway",
    version="0.1.0",
    description="API Gateway for ResearchAI - AI Research Paper Assistant",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": "gateway",
        "environment": settings.app_env,
        "version": "0.1.0",
    }


@app.get("/api/v1/health", tags=["System"])
async def api_v1_health():
    """Versioned API health check endpoint."""
    return {
        "status": "healthy",
        "service": "gateway",
        "api_version": "v1",
    }

