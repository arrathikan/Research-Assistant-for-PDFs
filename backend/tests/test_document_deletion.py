"""Permanent cleanup and races use unique disposable MongoDB databases, never user papers."""

from unittest.mock import patch

import pytest
from backend.gateway.documents import get_database
from backend.gateway.main import app
from backend.services.document_processor.chunk_storage import (
    chunk_stored_document,
    read_document_chunks,
)
from backend.services.document_processor.embedding_storage import save_embeddings
from backend.services.document_processor.extraction import parse_pdf
from backend.services.document_processor.parsed_models import (
    ParsedDocument,
    ParsedPage,
    ParsingError,
)
from backend.services.jobs.processor import process_message
from backend.services.jobs.store import ensure_requested
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable
from backend.shared.document_lifecycle import (
    DOCUMENT_COLLECTIONS,
    DocumentBusy,
    delete_document,
    document_write,
)
from backend.shared.job_models import JobMessage, job_id
from backend.shared.storage import (
    DocumentNotFound,
    find_document_by_hash,
    get_document,
    read_pdf,
)
from backend.shared.voyage import embedding_profile
from backend.tests.test_chunking_integration import database as mongo_database
from backend.tests.test_chunking_integration import seed_parse
from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError, NetworkTimeout, OperationFailure

pytestmark = pytest.mark.integration
SETTINGS = Settings(_env_file=None, llama_cloud_api_key="test-only-key")


@pytest.fixture
def database():
    yield from mongo_database.__wrapped__()


def test_cleanup_is_scoped_complete_and_idempotent(database):
    target, other = seed_parse(database), seed_parse(database)
    other_bytes = read_pdf(database, other)
    file_id = ObjectId(get_document(database, target).gridfs_file_id)
    for name in DOCUMENT_COLLECTIONS:
        for value in (target, ObjectId(target), other):
            database[name].insert_one({"document_id": value, "synthetic": True})
    database.embedding_vectors.insert_one({"_id": "shared-vector", "embedding": [0.1, 0.2]})
    before_indexes = database.chunk_embeddings.index_information()
    delete_document(database, target.upper())
    assert get_document(database, target) is None
    assert database["fs.files"].find_one({"_id": file_id}) is None
    assert database["fs.chunks"].count_documents({"files_id": file_id}) == 0
    for name in DOCUMENT_COLLECTIONS:
        assert (
            database[name].count_documents({"document_id": {"$in": [target, ObjectId(target)]}})
            == 0
        )
        assert database[name].count_documents({"document_id": other}) > 0
    assert database.embedding_vectors.count_documents({}) == 1
    assert database.chunk_embeddings.index_information() == before_indexes
    assert read_pdf(database, other) == other_bytes
    delete_document(database, target)


def test_live_short_write_blocks_deletion_until_released(database):
    identifier = seed_parse(database)
    with document_write(database, identifier):
        with pytest.raises(DocumentBusy):
            delete_document(database, identifier)
        assert get_document(database, identifier) is not None
    delete_document(database, identifier)
    with pytest.raises(DocumentNotFound):
        with document_write(database, identifier):
            pytest.fail("A late writer must never enter its persistence block")


def test_uncertain_writes_are_not_automatically_unlocked(database):
    identifier = seed_parse(database)
    with pytest.raises(NetworkTimeout):
        with document_write(database, identifier):
            raise NetworkTimeout("synthetic ambiguous write")
    assert database.documents.find_one({"_id": ObjectId(identifier)}).get("document_write_token")
    with pytest.raises(DocumentBusy):
        delete_document(database, identifier)


def test_acknowledged_storage_failure_releases_guard_for_normal_retry(database):
    identifier = seed_parse(database)
    with pytest.raises(OperationFailure):
        with document_write(database, identifier):
            raise OperationFailure("synthetic acknowledged rejection")
    assert "document_write_token" not in database.documents.find_one({"_id": ObjectId(identifier)})
    delete_document(database, identifier)


def test_partial_cleanup_is_retryable_and_blocks_workers_and_duplicate_uploads(database):
    identifier = seed_parse(database)
    original = get_document(database, identifier)
    ensure_requested(database, identifier, SETTINGS)
    delete_many = Collection.delete_many

    def fail_chunks(collection, *args, **kwargs):
        if collection.name == "chunks":
            raise OperationFailure("synthetic private storage error")
        return delete_many(collection, *args, **kwargs)

    with patch.object(Collection, "delete_many", fail_chunks):
        with pytest.raises(StorageUnavailable):
            delete_document(database, identifier)
    assert (
        database.documents.find_one({"_id": ObjectId(identifier)})["deletion_state"] == "DELETING"
    )
    assert get_document(database, identifier) is None
    with pytest.raises(StorageUnavailable):
        find_document_by_hash(database, original.sha256)
    with patch("backend.services.jobs.processor.parse_pdf") as provider:
        process_message(
            database, JobMessage(job_id=job_id(identifier), document_id=identifier), SETTINGS
        )
        provider.assert_not_called()
    delete_document(database, identifier)
    assert database.documents.find_one({"_id": ObjectId(identifier)}) is None


def test_late_parse_result_cannot_recreate_deleted_extraction(database):
    source = seed_parse(database)
    identifier = source
    database.documents.update_one(
        {"_id": ObjectId(identifier)},
        {
            "$set": {"status": "PENDING", "parsing_status": "NOT_STARTED"},
            "$unset": {"active_parse_run_id": ""},
        },
    )

    def parsed_after_deletion(*args):
        delete_document(database, identifier)
        return ParsedDocument(
            document_id=identifier,
            pages=[
                ParsedPage(
                    document_id=identifier, page_number=1, markdown="Synthetic delayed result"
                )
            ],
        )

    with patch(
        "backend.services.document_processor.extraction.parse_with_llamaparse",
        side_effect=parsed_after_deletion,
    ):
        with pytest.raises(ParsingError):
            parse_pdf(database, identifier, SETTINGS)
    assert database.documents.find_one({"_id": ObjectId(identifier)}) is None
    assert database.parsed_pages.count_documents({"document_id": identifier}) == 0
    assert database.source_elements.count_documents({"document_id": identifier}) == 0


def test_late_embedding_snapshot_and_job_retry_cannot_recreate_records(database):
    identifier = seed_parse(database)
    chunk_stored_document(database, identifier, SETTINGS)
    chunks = read_document_chunks(database, identifier)
    profile = embedding_profile(SETTINGS)
    from hashlib import sha256

    vectors = {
        sha256(chunk.content.encode()).hexdigest(): [0.1] * profile.dimensions for chunk in chunks
    }
    delete_document(database, identifier)
    with pytest.raises(DocumentNotFound):
        save_embeddings(database, chunks, vectors, profile)
    with pytest.raises(DocumentNotFound):
        ensure_requested(database, identifier, SETTINGS)
    assert database.chunk_embeddings.count_documents({"document_id": identifier}) == 0
    assert database.processing_jobs.count_documents({"document_id": identifier}) == 0


def test_gridfs_shared_by_another_document_is_preserved(database):
    target, other = seed_parse(database), seed_parse(database)
    selected = get_document(database, target)
    database.documents.update_one(
        {"_id": ObjectId(other)}, {"$set": {"gridfs_file_id": ObjectId(selected.gridfs_file_id)}}
    )
    expected = read_pdf(database, other)
    delete_document(database, target)
    assert read_pdf(database, other) == expected


def test_delete_http_contract_and_preflight(database):
    identifier = seed_parse(database)
    app.dependency_overrides[get_database] = lambda: database
    try:
        with TestClient(app) as client:
            with document_write(database, identifier):
                assert client.delete(f"/api/v1/documents/{identifier}").status_code == 409
            response = client.delete(f"/api/v1/documents/{identifier}")
            assert response.status_code == 204 and response.content == b""
            assert client.delete(f"/api/v1/documents/{identifier}").status_code == 204
            assert client.get(f"/api/v1/documents/{identifier}").status_code == 404
            assert client.delete("/api/v1/documents/invalid").status_code == 422
            preflight = client.options(
                f"/api/v1/documents/{identifier}",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "DELETE",
                },
            )
            assert preflight.status_code == 200
            assert "DELETE" in preflight.headers["access-control-allow-methods"]
    finally:
        app.dependency_overrides.clear()


def test_bulk_write_concern_failure_retains_the_guard(database):
    identifier = seed_parse(database)
    failure = BulkWriteError(
        {"writeErrors": [], "writeConcernErrors": [{"code": 64, "errmsg": "synthetic timeout"}]}
    )
    with pytest.raises(BulkWriteError):
        with document_write(database, identifier):
            raise failure
    with pytest.raises(DocumentBusy):
        delete_document(database, identifier)
