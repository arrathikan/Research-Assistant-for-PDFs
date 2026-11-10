"""Real pypdf-generated fixtures; no private PDFs or external parser calls."""

from io import BytesIO

import pytest
from backend.services.document_processor.upload import UploadRejected, validate_pdf
from pypdf import PdfWriter


def pdf_bytes(pages: int = 1, encrypted: bool = False) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=200, height=300)
    if encrypted:
        writer.encrypt("test-password")
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_valid_pdf_and_safe_basename():
    content = pdf_bytes(pages=2)
    result = validate_pdf(
        "C:\\private\\paper.PDF", "application/pdf", BytesIO(content), len(content)
    )
    assert result.filename == "paper.PDF"
    assert result.page_count == 2
    assert result.content == content


@pytest.mark.parametrize("mime", [None, "", "application/octet-stream"])
def test_missing_or_generic_mime_still_requires_valid_pdf(mime):
    content = pdf_bytes()
    assert validate_pdf("paper.pdf", mime, BytesIO(content), 1024).page_count == 1


@pytest.mark.parametrize("filename", ["paper.txt", "", None, "bad\nname.pdf"])
def test_rejects_invalid_filename(filename):
    with pytest.raises(UploadRejected):
        validate_pdf(filename, "application/pdf", BytesIO(pdf_bytes()), 1024)


def test_rejects_wrong_mime():
    with pytest.raises(UploadRejected) as error:
        validate_pdf("paper.pdf", "text/plain", BytesIO(pdf_bytes()), 1024)
    assert error.value.status_code == 415


def test_rejects_empty_content():
    with pytest.raises(UploadRejected, match="empty"):
        validate_pdf("paper.pdf", "application/pdf", BytesIO(), 1024)


def test_reads_at_most_limit_plus_one_byte():
    stream = BytesIO(b"x" * 10000)
    with pytest.raises(UploadRejected) as error:
        validate_pdf("paper.pdf", "application/pdf", stream, 100)
    assert error.value.status_code == 413
    assert stream.tell() == 101


@pytest.mark.parametrize(
    "content", [b"not a pdf", b"%PDF-1.7\ntruncated", b"%PDF-1.7\nbroken xref\n%%EOF"]
)
def test_rejects_spoofed_truncated_or_corrupt_content(content):
    with pytest.raises(UploadRejected):
        validate_pdf("paper.pdf", "application/pdf", BytesIO(content), 1024)


def test_rejects_encrypted_pdf():
    with pytest.raises(UploadRejected, match="Encrypted"):
        validate_pdf("paper.pdf", "application/pdf", BytesIO(pdf_bytes(encrypted=True)), 4096)


def test_rejects_zero_page_pdf():
    with pytest.raises(UploadRejected, match="at least one page"):
        validate_pdf("paper.pdf", "application/pdf", BytesIO(pdf_bytes(pages=0)), 1024)
