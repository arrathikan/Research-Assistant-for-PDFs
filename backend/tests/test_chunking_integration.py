"""Real MongoDB chunk lifecycle with synthetic parsed artifacts; no provider calls."""

import os
from io import BytesIO
from unittest.mock import patch
from uuid import uuid4

import pytest
from backend.gateway.documents import get_database
from backend.gateway.main import app
from backend.services.document_processor.chunk_models import ChunkingError
from backend.services.document_processor.chunk_storage import (
    ChunkingConflict,
    ChunkingNotReady,
    chunk_stored_document,
    read_document_chunks,
)
from backend.services.document_processor.extraction import (
    ensure_parse_indexes,
    save_parsed_document,
)
from backend.services.document_processor.normalization import normalize_parsed_pages
from backend.shared.config import Settings
from backend.shared.database import (
    StorageUnavailable,
    connect_database,
    ensure_chunk_indexes,
    ensure_indexes,
)
from backend.shared.storage import get_document, store_pdf
from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo.collection import Collection
from pymongo.errors import OperationFailure
from pypdf import PdfWriter

pytestmark = pytest.mark.integration
SETTINGS = Settings(_env_file=None, llama_cloud_api_key="", voyage_api_key="")


@pytest.fixture
def database():
    uri = os.environ.get("RESEARCHAI_TEST_MONGODB_URI")
    if not uri:
        pytest.skip("Set RESEARCHAI_TEST_MONGODB_URI for isolated MongoDB tests")
    config = Settings(
        _env_file=None, mongodb_uri=uri, mongodb_db_name="researchai_test_" + uuid4().hex
    )
    with connect_database(config) as db:
        try:
            ensure_indexes(db)
            yield db
        finally:
            db.client.drop_database(db.name)


def seed_parse(database):
    output = BytesIO()
    writer = PdfWriter()
    for _ in range(2):
        writer.add_blank_page(width=200, height=300)
    writer.add_metadata({"/Title": "Synthetic chunk fixture " + uuid4().hex})
    writer.write(output)
    identifier = store_pdf(database, "synthetic.pdf", output.getvalue(), page_count=2).document.id
    run = uuid4().hex
    ensure_parse_indexes(database)
    database.documents.update_one(
        {"_id": ObjectId(identifier)},
        {"$set": {"status": "PARSING", "parsing_status": "RUNNING", "parsing_run_id": run}},
    )
    parsed = normalize_parsed_pages(
        identifier,
        [
            {
                "pages": [
                    {
                        "page": 1,
                        "md": "## Method\n\nUnique evidence sentence describing this method.",
                        "items": [
                            {
                                "type": "text",
                                "text": "Unique evidence sentence describing this method.",
                                "bBox": {"x": 10, "y": 20, "w": 100, "h": 15},
                            }
                        ],
                    },
                    {
                        "page": 2,
                        "md": "Continuation on the next page with additional method details.\n\n## Results\n\n| Model | Score |\n| --- | --- |\n| A | 42 |",
                    },
                ]
            }
        ],
        2,
    )
    save_parsed_document(database, parsed, run, SETTINGS)
    return identifier


def test_real_chunk_persistence_reuse_and_endpoint(database):
    identifier = seed_parse(database)
    first = chunk_stored_document(database, identifier, SETTINGS)
    assert read_document_chunks(database, identifier) == first
    assert [chunk.id for chunk in chunk_stored_document(database, identifier, SETTINGS)] == [
        chunk.id for chunk in first
    ]
    assert database.chunks.count_documents({"document_id": identifier}) == len(first)
    assert any(chunk.page_numbers == [1, 2] for chunk in first)
    metadata = get_document(database, identifier)
    assert metadata.chunking_status == "COMPLETED" and metadata.status == "PENDING"
    assert metadata.chunked_at is not None
    app.dependency_overrides[get_database] = lambda: database
    try:
        with TestClient(app) as client:
            response = client.get(f"/api/v1/documents/{identifier}/chunks")
            assert response.status_code == 200
            assert response.json()[0]["id"] == first[0].id
    finally:
        app.dependency_overrides.clear()


def test_new_configuration_preserves_prior_chunks(database):
    identifier = seed_parse(database)
    first = chunk_stored_document(database, identifier, SETTINGS)
    settings = Settings(_env_file=None, chunk_size=50, chunk_overlap=10)
    second = chunk_stored_document(database, identifier, settings)
    assert first[0].chunk_set_id != second[0].chunk_set_id
    assert database.chunks.count_documents({"document_id": identifier}) == len(first) + len(second)
    assert all(len(chunk.content) <= 50 for chunk in second)
    assert read_document_chunks(database, identifier) == second


def test_partial_write_failure_keeps_previous_active_set_and_retries_safely(database):
    identifier = seed_parse(database)
    original_chunks = chunk_stored_document(database, identifier, SETTINGS)
    settings = Settings(_env_file=None, chunk_size=50, chunk_overlap=10)
    original_bulk = Collection.bulk_write

    def partial_write(collection, operations, *args, **kwargs):
        original_bulk(collection, operations[:1], *args, **kwargs)
        raise OperationFailure("synthetic partial write")

    with patch.object(Collection, "bulk_write", partial_write):
        with pytest.raises(ChunkingError):
            chunk_stored_document(database, identifier, settings)
    assert read_document_chunks(database, identifier) == original_chunks
    assert get_document(database, identifier).chunking_status == "FAILED"
    retried = chunk_stored_document(database, identifier, settings)
    assert retried[0].chunk_set_id != original_chunks[0].chunk_set_id
    assert database.chunks.count_documents({"document_id": identifier}) == len(
        original_chunks
    ) + len(retried)


def test_running_claim_blocks_a_second_writer(database):
    identifier = seed_parse(database)
    database.documents.update_one(
        {"_id": ObjectId(identifier)},
        {"$set": {"chunking_status": "RUNNING", "chunking_run_id": "another-worker"}},
    )
    with pytest.raises(ChunkingConflict):
        chunk_stored_document(database, identifier, SETTINGS)
    assert database.chunks.count_documents({}) == 0


def test_parse_change_prevents_publication(database):
    identifier = seed_parse(database)
    original_bulk = Collection.bulk_write

    def changed_parse(collection, operations, *args, **kwargs):
        result = original_bulk(collection, operations, *args, **kwargs)
        database.documents.update_one(
            {"_id": ObjectId(identifier)}, {"$set": {"active_parse_run_id": "changed-parse"}}
        )
        return result

    with patch.object(Collection, "bulk_write", changed_parse):
        with pytest.raises(ChunkingError):
            chunk_stored_document(database, identifier, SETTINGS)
    with pytest.raises(ChunkingNotReady):
        read_document_chunks(database, identifier)
    assert (
        database.documents.find_one({"_id": ObjectId(identifier)}).get("active_chunk_set_id")
        is None
    )


def test_document_and_source_isolation(database):
    first, second = seed_parse(database), seed_parse(database)
    first_chunks = chunk_stored_document(database, first, SETTINGS)
    second_chunks = chunk_stored_document(database, second, SETTINGS)
    assert {chunk.id for chunk in first_chunks}.isdisjoint({chunk.id for chunk in second_chunks})
    assert all(chunk.document_id == first for chunk in read_document_chunks(database, first))
    assert all(
        source.document_id == first
        for chunk in first_chunks
        for span in chunk.page_spans
        for source in span.source_elements
    )


def test_empty_legacy_chunk_index_upgrade(database):
    database.chunks.create_index(
        [("document_id", 1), ("chunk_index", 1)], unique=True, name="document_chunk_index"
    )
    ensure_chunk_indexes(database)
    assert "document_chunk_index" not in database.chunks.index_information()
    assert database.chunks.index_information()["document_chunk_set_index"]["unique"] is True


def test_populated_legacy_data_is_preserved_for_review(database):
    database.chunks.insert_one({"_id": "legacy", "document_id": "legacy", "chunk_index": 0})
    database.chunks.create_index(
        [("document_id", 1), ("chunk_index", 1)], unique=True, name="document_chunk_index"
    )
    with pytest.raises(StorageUnavailable, match="reviewed migration"):
        ensure_chunk_indexes(database)
    assert database.chunks.count_documents({}) == 1
    assert "document_chunk_index" in database.chunks.index_information()
