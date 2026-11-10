"""Opt-in real MongoDB tests, always using a uniquely named disposable database."""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, local
from uuid import uuid4

import pytest
from backend.shared import storage
from backend.shared.config import Settings
from backend.shared.database import connect_database, ensure_indexes
from gridfs import GridFSBucket

pytestmark = pytest.mark.integration


@pytest.fixture
def database():
    uri = os.environ.get("RESEARCHAI_TEST_MONGODB_URI")
    if not uri:
        pytest.skip("Set RESEARCHAI_TEST_MONGODB_URI to opt into live MongoDB tests")
    settings = Settings(
        _env_file=None,
        mongodb_uri=uri,
        mongodb_db_name="researchai_test_" + uuid4().hex,
    )
    with connect_database(settings) as database:
        try:
            ensure_indexes(database)
            yield database
        finally:
            # Only this fixture's freshly generated database is ever dropped.
            database.client.drop_database(database.name)


def test_live_indexes_are_idempotent(database):
    ensure_indexes(database)
    assert set(database.list_collection_names()) >= {
        "documents",
        "chunks",
        "source_elements",
        "summaries",
        "chat_messages",
        "processing_jobs",
    }
    assert database.documents.index_information()["unique_sha256"]["unique"] is True
    assert database.chunks.index_information()["document_chunk_index"]["unique"] is True


def test_live_gridfs_round_trip_larger_than_bson_limit(database):
    # Synthetic storage bytes, not a parser fixture or a private research paper.
    content = b"%PDF-1.7\n" + b"x" * (17 * 1024 * 1024)
    result = storage.store_pdf(database, "synthetic.pdf", content)
    assert result.is_duplicate is False
    assert storage.read_pdf(database, result.document.id) == content
    duplicate = storage.store_pdf(database, "renamed.pdf", content)
    assert duplicate.is_duplicate is True
    assert duplicate.document.id == result.document.id
    assert database.documents.count_documents({}) == 1
    assert database.fs.files.count_documents({}) == 1
    assert database.fs.chunks.count_documents({}) > 1
    GridFSBucket(database).delete(storage._object_id(result.document.gridfs_file_id))
    with pytest.raises(storage.DocumentNotFound, match="Original PDF not found"):
        storage.read_pdf(database, result.document.id)


def test_live_concurrent_duplicates_leave_one_file(database, monkeypatch):
    workers = 8
    barrier = Barrier(workers, timeout=20)
    thread_state = local()
    original_lookup = storage.find_document_by_hash

    def simultaneous_first_lookup(db, digest):
        result = original_lookup(db, digest)
        if not getattr(thread_state, "looked_up", False):
            thread_state.looked_up = True
            # Force every writer past the initial miss before any file is saved.
            assert result is None
            barrier.wait()
        return result

    monkeypatch.setattr(storage, "find_document_by_hash", simultaneous_first_lookup)
    content = b"%PDF-1.7\nConcurrent storage fixture"
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(
            pool.map(lambda _: storage.store_pdf(database, "race.pdf", content), range(workers))
        )
    assert len({result.document.id for result in results}) == 1
    assert sum(not result.is_duplicate for result in results) == 1
    assert database.documents.count_documents({}) == 1
    assert database.fs.files.count_documents({}) == 1
    assert database.fs.chunks.count_documents({}) == 1
    assert storage.read_pdf(database, results[0].document.id) == content
