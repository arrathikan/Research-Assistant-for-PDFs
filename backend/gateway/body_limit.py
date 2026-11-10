"""Bound multipart upload bodies, including requests without Content-Length."""

from backend.shared.config import get_settings
from fastapi.responses import JSONResponse
from starlette.formparsers import MultiPartException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

LIMIT_DETAIL = "Upload request exceeds the configured size limit"
UPLOAD_PATHS = {"/api/v1/documents", "/api/v1/documents/upload"}
MULTIPART_OVERHEAD_BYTES = 64 * 1024


class UploadBodyLimit:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope["method"] != "POST"
            or scope["path"].rstrip("/") not in UPLOAD_PATHS
        ):
            await self.app(scope, receive, send)
            return
        limit = get_settings().max_upload_size_bytes + MULTIPART_OVERHEAD_BYTES
        headers = dict(scope["headers"])
        length = headers.get(b"content-length")
        if length is not None:
            try:
                size = int(length)
                if size < 0:
                    raise ValueError
            except ValueError:
                await JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)(
                    scope, receive, send
                )
                return
            if size > limit:
                await JSONResponse({"detail": LIMIT_DETAIL}, status_code=413)(scope, receive, send)
                return
        received = 0

        async def bounded_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    # The multipart parser catches this type and closes partial
                    # spool files. The upload route maps this specific error to 413.
                    raise MultiPartException(LIMIT_DETAIL)
            return message

        await self.app(scope, bounded_receive, send)
