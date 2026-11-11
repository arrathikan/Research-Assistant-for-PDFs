"""Current citation resolution against persisted chunks and the public API."""

import pytest
from backend.gateway.documents import get_database
from backend.gateway.main import app
from backend.services.document_processor.chunk_storage import chunk_stored_document
from backend.services.rag_service.citations import CitationSelection, make_citation
from backend.shared.config import Settings
from backend.tests.test_chunking_integration import SETTINGS, seed_parse
from backend.tests.test_chunking_integration import database as mongo_database
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration
QUOTE = "Unique evidence sentence describing this method."


@pytest.fixture
def database():
    yield from mongo_database.__wrapped__()


def selection(database):
    identifier = seed_parse(database)
    chunk = chunk_stored_document(database, identifier, SETTINGS)[0]
    anchor = make_citation(chunk, 1, QUOTE)
    body = CitationSelection.model_validate(
        anchor.model_dump(include=set(CitationSelection.model_fields))
    ).model_dump()
    return identifier, anchor, body


def request(database, identifier, body):
    app.dependency_overrides[get_database] = lambda: database
    try:
        with TestClient(app) as client:
            return client.post(f"/api/v1/documents/{identifier}/citations/resolve", json=body)
    finally:
        app.dependency_overrides.clear()


def test_current_source_resolves_from_persisted_chunks_without_model(database):
    identifier, anchor, body = selection(database)
    response = request(database, identifier, body)
    assert response.status_code == 200
    assert response.json() == anchor.model_dump(mode="json")
    assert response.json()["chunk_set_id"]
    assert response.json()["quote_snippet"] == QUOTE


def test_rechunked_source_cannot_reopen_an_old_citation(database):
    identifier, _, body = selection(database)
    chunk_stored_document(
        database, identifier, Settings(_env_file=None, chunk_size=50, chunk_overlap=10)
    )
    assert request(database, identifier, body).status_code == 409


def test_other_document_and_client_supplied_geometry_are_rejected(database):
    identifier, _, body = selection(database)
    other = seed_parse(database)
    assert request(database, other, body).status_code == 422
    assert request(database, identifier, {**body, "bounding_boxes": []}).status_code == 422
