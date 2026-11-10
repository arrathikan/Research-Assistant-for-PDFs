"""Validate one upload before any database writes or processing calls."""

from io import BytesIO
from pathlib import PurePosixPath
from struct import error as StructError
from typing import BinaryIO

from pydantic import BaseModel, Field
from pypdf import PdfReader
from pypdf.errors import PyPdfError


class UploadRejected(ValueError):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class ValidatedPdf(BaseModel):
    filename: str
    content: bytes = Field(repr=False)
    page_count: int = Field(gt=0)


def validate_pdf(
    filename: str | None, content_type: str | None, stream: BinaryIO, max_size: int
) -> ValidatedPdf:
    """Bound the read, check file type, and validate the PDF structure/page tree.

    This is not rendering, malware scanning, or academic-content verification.
    Strict parsing intentionally rejects PDFs that need automatic repair.
    """
    name = PurePosixPath((filename or "").replace("\\", "/")).name.strip()
    if not name.lower().endswith(".pdf") or len(name) > 255 or any(ord(c) < 32 for c in name):
        raise UploadRejected("Choose a PDF file with a valid .pdf filename")
    if content_type not in (None, "", "application/pdf", "application/octet-stream"):
        raise UploadRejected("Only PDF uploads are supported", 415)
    content = stream.read(max_size + 1)
    if len(content) > max_size:
        raise UploadRejected("PDF exceeds the configured upload size limit", 413)
    if not content:
        raise UploadRejected("The PDF file is empty")
    if not content.startswith(b"%PDF-") or not content.rstrip().endswith(b"%%EOF"):
        raise UploadRejected("The file is not a complete PDF")
    try:
        reader = PdfReader(BytesIO(content), strict=True)
        if reader.is_encrypted:
            raise UploadRejected("Encrypted PDFs are not supported; upload an unencrypted copy")
        count = len(reader.pages)
        if count == 0:
            raise UploadRejected("The PDF must contain at least one page")
        for page in reader.pages:
            # Resolve page objects and dimensions without decompressing text/image streams.
            if page.mediabox.width <= 0 or page.mediabox.height <= 0:
                raise UploadRejected("The PDF contains an invalid page")
    except (
        PyPdfError,
        KeyError,
        TypeError,
        ValueError,
        RecursionError,
        OverflowError,
        StructError,
    ) as exc:
        if isinstance(exc, UploadRejected):
            raise
        raise UploadRejected("The PDF is corrupt or unsupported") from None
    return ValidatedPdf(filename=name, content=content, page_count=count)
