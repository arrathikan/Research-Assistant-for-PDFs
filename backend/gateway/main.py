"""ResearchAI HTTP gateway with consistent, privacy-conscious error responses."""

from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from backend.gateway.body_limit import UploadBodyLimit
from backend.gateway.chat import router as chat_router
from backend.gateway.citations import router as citations_router
from backend.gateway.documents import router as documents_router
from backend.gateway.health import router
from backend.gateway.schemas import ErrorResponse
from backend.services.document_processor.upload import UploadRejected
from backend.shared.config import get_settings
from backend.shared.database import StorageUnavailable
from backend.shared.logging import setup_logger
from backend.shared.storage import DocumentNotFound
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException

settings = get_settings()
logger = setup_logger("gateway", settings.log_level)


def create_app() -> FastAPI:
    """Build an application without connecting to external infrastructure."""
    application = FastAPI(
        title="ResearchAI Gateway",
        version="0.1.0",
        description="API Gateway for ResearchAI - AI Research Paper Assistant",
        responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    )
    application.include_router(router)
    application.include_router(documents_router)
    application.include_router(chat_router)
    application.include_router(citations_router)
    application.add_middleware(UploadBodyLimit)

    @application.exception_handler(UploadRejected)
    async def upload_error(request: Request, exc: UploadRejected) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @application.exception_handler(StorageUnavailable)
    async def storage_error(request: Request, exc: StorageUnavailable) -> JSONResponse:
        return JSONResponse(
            status_code=503, content={"detail": "Document storage temporarily unavailable"}
        )

    @application.exception_handler(DocumentNotFound)
    async def missing_original(request: Request, exc: DocumentNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Original PDF not found"})

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail},
            headers=exc.headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Never reflect request bodies, credentials, or uploaded content in errors.
        return JSONResponse(status_code=422, content={"detail": "Invalid request"})

    @application.middleware("http")
    async def log_request(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid4())
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # Avoid logging exception messages that can contain provider credentials.
            logger.error("Unhandled gateway failure", extra={"request_id": request_id})
            response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": round((perf_counter() - started) * 1000, 2),
            },
        )
        return response

    return application


# Wrap the whole app so CORS also applies to unexpected error responses.
app = create_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
    expose_headers=["X-Request-ID"],
)
