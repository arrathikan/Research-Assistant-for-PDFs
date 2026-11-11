"""Upload HTTP tests with real validation and a mocked persistence boundary."""

from hashlib import sha256
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from backend.gateway.documents import get_database
from backend.gateway.main import app
from backend.shared.config import get_settings
from backend.shared.database import StorageUnavailable
from backend.shared.storage import DocumentNotFound, StoredDocument, StoredPdfResult
from bson import ObjectId
from fastapi.testclient import TestClient
from pypdf import PdfWriter


@pytest.fixture
def pdf():
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=300)
    writer.write(output)
    return output.getvalue()


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def document(pdf):
    return StoredDocument(
        id=str(ObjectId()),
        gridfs_file_id=str(ObjectId()),
        sha256=sha256(pdf).hexdigest(),
        filename="paper.pdf",
        file_size_bytes=len(pdf),
        page_count=1,
    )


@pytest.mark.parametrize("endpoint", ["/api/v1/documents", "/api/v1/documents/upload"])
@pytest.mark.parametrize("duplicate,code", [(False, 201), (True, 200)])
def test_upload_and_duplicate_contract(client, pdf, endpoint, duplicate, code):
    doc = document(pdf)
    with (
        patch("backend.gateway.upload_service.connect_database") as connection,
        patch("backend.gateway.upload_service.ensure_indexes") as indexes,
        patch("backend.gateway.upload_service.store_pdf") as store,
        patch("backend.gateway.upload_service.ensure_requested") as schedule,
    ):
        database = connection.return_value.__enter__.return_value
        store.return_value = StoredPdfResult(document=doc, is_duplicate=duplicate)
        response = client.post(endpoint, files={"file": ("paper.pdf", pdf, "application/pdf")})
        assert response.status_code == code
        data = response.json()
        assert data["document"]["id"] == doc.id
        assert "_id" not in data["document"]
        assert data["document"]["status"] == "PENDING"
        assert data["is_duplicate"] is duplicate
        assert data["message"]
        schedule.assert_called_once_with(database, doc.id, get_settings())
        indexes.assert_called_once_with(database)
        store.assert_called_once_with(database, "paper.pdf", pdf, page_count=1)


@pytest.mark.parametrize(
    "name,content,mime,code",
    [
        ("bad.txt", b"text", "text/plain", 400),
        ("empty.pdf", b"", "application/pdf", 400),
        ("fake.pdf", b"not a pdf", "application/pdf", 400),
        ("paper.pdf", b"%PDF-1.7\nbad\n%%EOF", "application/pdf", 400),
    ],
)
def test_invalid_file_never_connects_to_storage(client, name, content, mime, code):
    with patch("backend.gateway.upload_service.connect_database") as connection:
        response = client.post("/api/v1/documents", files={"file": (name, content, mime)})
    assert response.status_code == code
    assert isinstance(response.json()["detail"], str)
    connection.assert_not_called()


def test_storage_failure_is_safe_503(client, pdf):
    with patch(
        "backend.gateway.upload_service.connect_database",
        side_effect=StorageUnavailable("private-path"),
    ):
        response = client.post(
            "/api/v1/documents", files={"file": ("paper.pdf", pdf, "application/pdf")}
        )
    assert response.status_code == 503
    assert response.json() == {"detail": "Document storage temporarily unavailable"}


@pytest.mark.parametrize(
    "files",
    [
        [],
        [("wrong", ("a.pdf", b"x", "application/pdf"))],
        [
            ("file", ("a.pdf", b"x", "application/pdf")),
            ("file", ("b.pdf", b"x", "application/pdf")),
        ],
    ],
)
def test_rejects_missing_wrong_or_multiple_files(client, files):
    response = client.post("/api/v1/documents", files=files)
    assert response.status_code in (400, 415, 422)


def test_file_limit_rejects_before_storage(client, monkeypatch, pdf):
    from backend.shared.config import get_settings

    monkeypatch.setattr(get_settings(), "max_upload_size_bytes", 100)
    with patch("backend.gateway.upload_service.connect_database") as connection:
        response = client.post(
            "/api/v1/documents", files={"file": ("paper.pdf", pdf, "application/pdf")}
        )
    assert response.status_code == 413
    connection.assert_not_called()


def test_body_limit_checks_actual_bytes_without_content_length(client, monkeypatch):
    from backend.shared.config import get_settings

    monkeypatch.setattr(get_settings(), "max_upload_size_bytes", 100)
    body = (
        b'--b\r\nContent-Disposition: form-data; name="file"; filename="paper.pdf"\r\nContent-Type: application/pdf\r\n\r\n'
        + b"x" * 70000
        + b"\r\n--b--\r\n"
    )
    with patch("backend.gateway.upload_service.connect_database") as connection:
        response = client.post(
            "/api/v1/documents",
            content=iter([body[:200], body[200:]]),
            headers={"Content-Type": "multipart/form-data; boundary=b"},
        )
    assert response.status_code == 413
    connection.assert_not_called()


def test_declared_body_limit_and_invalid_content_length(client, monkeypatch):
    from backend.shared.config import get_settings

    monkeypatch.setattr(get_settings(), "max_upload_size_bytes", 100)
    assert (
        client.post(
            "/api/v1/documents", content=b"", headers={"Content-Length": "1000000"}
        ).status_code
        == 413
    )
    assert (
        client.post("/api/v1/documents", content=b"", headers={"Content-Length": "-1"}).status_code
        == 400
    )


def test_metadata_status_and_pdf_contracts(client, pdf):
    doc = document(pdf)
    database = MagicMock()
    app.dependency_overrides[get_database] = lambda: database
    with (
        patch("backend.gateway.documents.get_document", return_value=doc),
        patch("backend.gateway.documents.read_pdf", return_value=pdf),
    ):
        assert client.get(f"/api/v1/documents/{doc.id}").json()["id"] == doc.id
        status = client.get(f"/api/v1/documents/{doc.id}/status").json()
        assert status == {"document_id": doc.id, "status": "PENDING", "error_message": None}
        response = client.get(f"/api/v1/documents/{doc.id}/pdf")
        assert response.content == pdf
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["content-disposition"].startswith("inline;")


def test_missing_document_and_invalid_identifier(client):
    app.dependency_overrides[get_database] = lambda: MagicMock()
    with patch("backend.gateway.documents.get_document", return_value=None):
        for suffix in ("", "/status", "/pdf"):
            assert client.get(f"/api/v1/documents/{ObjectId()}{suffix}").status_code == 404
        assert client.get("/api/v1/documents/not-an-id").status_code == 422


def test_missing_gridfs_original_returns_404(client, pdf):
    doc = document(pdf)
    app.dependency_overrides[get_database] = lambda: MagicMock()
    with (
        patch("backend.gateway.documents.get_document", return_value=doc),
        patch("backend.gateway.documents.read_pdf", side_effect=DocumentNotFound()),
    ):
        assert client.get(f"/api/v1/documents/{doc.id}/pdf").status_code == 404
