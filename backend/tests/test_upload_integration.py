"""Opt-in real upload API + MongoDB tests; no mocked persistence or private PDFs."""

import os
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
from threading import Barrier, local
from uuid import uuid4

import pytest
from backend.gateway.main import app
from backend.shared import storage
from backend.shared.config import get_settings
from backend.shared.database import connect_database
from fastapi.testclient import TestClient
from pypdf import PdfWriter

pytestmark = pytest.mark.integration


@pytest.fixture
def live_upload_database(monkeypatch):
    uri = os.environ.get("RESEARCHAI_TEST_MONGODB_URI")
    if not uri:
        pytest.skip("Set RESEARCHAI_TEST_MONGODB_URI to opt into live MongoDB tests")
    settings = get_settings()
    monkeypatch.setattr(settings, "mongodb_uri", uri)
    monkeypatch.setattr(settings, "mongodb_db_name", "researchai_test_" + uuid4().hex)
    with connect_database(settings) as database:
        try:
            # The real upload API is responsible for initializing its indexes.
            yield database
        finally:
            database.client.drop_database(database.name)


@pytest.fixture
def real_pdf():
    output = BytesIO()
    writer = PdfWriter()
    for _ in range(2):
        writer.add_blank_page(width=200, height=300)
    writer.write(output)
    return output.getvalue()


def test_live_upload_duplicate_status_and_original(live_upload_database, real_pdf):
    with TestClient(app) as client:
        first = client.post(
            "/api/v1/documents", files={"file": ("paper.pdf", real_pdf, "application/pdf")}
        )
        assert first.status_code == 201
        data = first.json()
        document = data["document"]
        identifier = document["id"]
        assert document["sha256"] == sha256(real_pdf).hexdigest()
        assert document["page_count"] == 2
        assert document["status"] == "PENDING"
        assert data["is_duplicate"] is False
        duplicate = client.post(
            "/api/v1/documents/upload", files={"file": ("renamed.pdf", real_pdf, "application/pdf")}
        )
        assert duplicate.status_code == 200
        assert duplicate.json()["document"]["id"] == identifier
        assert duplicate.json()["is_duplicate"] is True
        assert client.get(f"/api/v1/documents/{identifier}").json() == document
        assert client.get(f"/api/v1/documents/{identifier}/status").json()["status"] == "PENDING"
        original = client.get(f"/api/v1/documents/{identifier}/pdf")
        assert original.status_code == 200
        assert original.content == real_pdf
    assert live_upload_database.documents.count_documents({}) == 1
    assert live_upload_database.fs.files.count_documents({}) == 1


def test_live_concurrent_upload_requests(live_upload_database, real_pdf, monkeypatch):
    workers = 6
    barrier = Barrier(workers, timeout=20)
    state = local()
    original_lookup = storage.find_document_by_hash

    def first_lookup_together(database, digest):
        result = original_lookup(database, digest)
        if not getattr(state, "queried", False):
            state.queried = True
            assert result is None
            barrier.wait()
        return result

    monkeypatch.setattr(storage, "find_document_by_hash", first_lookup_together)

    def upload(_):
        with TestClient(app) as client:
            return client.post(
                "/api/v1/documents", files={"file": ("race.pdf", real_pdf, "application/pdf")}
            )

    with ThreadPoolExecutor(max_workers=workers) as pool:
        responses = list(pool.map(upload, range(workers)))
    assert sorted(response.status_code for response in responses) == [200] * (workers - 1) + [201]
    assert len({response.json()["document"]["id"] for response in responses}) == 1
    assert live_upload_database.documents.count_documents({}) == 1
    assert live_upload_database.fs.files.count_documents({}) == 1
    assert live_upload_database.fs.chunks.count_documents({}) == 1


def test_live_rejected_uploads_write_nothing(live_upload_database, real_pdf, monkeypatch):
    with TestClient(app) as client:
        assert (
            client.post(
                "/api/v1/documents", files={"file": ("fake.pdf", b"not a PDF", "application/pdf")}
            ).status_code
            == 400
        )
        assert (
            client.post(
                "/api/v1/documents",
                files=[
                    ("file", ("one.pdf", real_pdf, "application/pdf")),
                    ("file", ("two.pdf", real_pdf, "application/pdf")),
                ],
            ).status_code
            == 400
        )
        monkeypatch.setattr(get_settings(), "max_upload_size_bytes", 10)
        assert (
            client.post(
                "/api/v1/documents", files={"file": ("big.pdf", real_pdf, "application/pdf")}
            ).status_code
            == 413
        )
    assert live_upload_database.documents.count_documents({}) == 0
    assert live_upload_database.fs.files.count_documents({}) == 0
