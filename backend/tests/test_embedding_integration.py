"""Real Mongo persistence with synthetic chunks and deterministic provider vectors."""

from unittest.mock import patch

import pytest
from backend.services.document_processor.chunk_storage import chunk_stored_document
from backend.services.document_processor.embedding_storage import (
    embed_stored_document,
    read_embedding_summary,
)
from backend.shared.config import Settings
from backend.shared.embedding_models import EmbeddingError
from backend.tests.test_chunking_integration import database as mongo_database
from backend.tests.test_chunking_integration import seed_parse
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import OperationFailure

pytestmark = pytest.mark.integration
SETTINGS = Settings(_env_file=None, voyage_api_key="synthetic-key", voyage_batch_size=1)
PROVIDER = "backend.services.document_processor.embedding_storage.embed_documents"


@pytest.fixture
def database():
    yield from mongo_database.__wrapped__()


def vectors(texts, settings):
    return [[0.1] * settings.voyage_dimensions for _ in texts]


def prepare(database, settings=SETTINGS):
    identifier = seed_parse(database)
    chunks = chunk_stored_document(database, identifier, settings)
    return identifier, chunks


def test_real_storage_reuses_content_across_documents_and_keeps_sources(database):
    first, chunks = prepare(database)
    second, other_chunks = prepare(database)
    with patch(PROVIDER, side_effect=vectors) as provider:
        done = embed_stored_document(database, first, SETTINGS)
        calls = provider.call_count
        assert calls > 0
        assert embed_stored_document(database, first, SETTINGS) == done
        embed_stored_document(database, second, SETTINGS)
        assert provider.call_count == calls
    records = list(database.chunk_embeddings.find({"document_id": first}))
    assert {record["chunk_id"] for record in records} == {chunk.id for chunk in chunks}
    assert all(record["chunk"]["page_spans"] for record in records)
    assert all(record["chunk"]["document_id"] == first for record in records)
    assert database.chunks.count_documents({}) == len(chunks) + len(other_chunks)
    assert database.documents.find_one({"_id": ObjectId(first)})["status"] == "PENDING"
    assert all("content" not in row for row in database.embedding_vectors.find({}))


def test_real_partial_provider_failure_reuses_cached_batch_on_retry(database):
    settings = SETTINGS.model_copy(update={"chunk_size": 50, "chunk_overlap": 10})
    identifier, chunks = prepare(database, settings)
    assert len(chunks) > 1
    calls = 0

    def partial(texts, config):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise EmbeddingError("synthetic interruption")
        return vectors(texts, config)

    with patch(PROVIDER, side_effect=partial):
        with pytest.raises(EmbeddingError):
            embed_stored_document(database, identifier, settings)
    assert database.embedding_vectors.count_documents({}) == 1
    assert database.chunk_embeddings.count_documents({}) == 0
    assert (
        database.documents.find_one({"_id": ObjectId(identifier)})["embedding_status"] == "FAILED"
    )
    with patch(PROVIDER, side_effect=vectors) as provider:
        done = embed_stored_document(database, identifier, settings)
        assert provider.call_count == len({chunk.content for chunk in chunks}) - 1
    assert done.chunk_count == len(chunks)


def test_real_snapshot_failure_never_publishes_and_retry_uses_cache(database):
    identifier, _ = prepare(database)
    with (
        patch(PROVIDER, side_effect=vectors),
        patch.object(Collection, "bulk_write", side_effect=OperationFailure("synthetic failure")),
    ):
        with pytest.raises(EmbeddingError):
            embed_stored_document(database, identifier, SETTINGS)
    record = database.documents.find_one({"_id": ObjectId(identifier)})
    assert "active_embedding_profile_id" not in record
    with patch(PROVIDER) as provider:
        embed_stored_document(database, identifier, SETTINGS)
        provider.assert_not_called()
    assert read_embedding_summary(database, identifier, SETTINGS).chunk_count > 0


def test_real_model_change_creates_separate_profile_without_overwriting(database):
    identifier, chunks = prepare(database)
    other = SETTINGS.model_copy(update={"voyage_model": "voyage-large-2-instruct"})
    with patch(PROVIDER, side_effect=vectors):
        first = embed_stored_document(database, identifier, SETTINGS)
        second = embed_stored_document(database, identifier, other)
    assert first.embedding_profile_id != second.embedding_profile_id
    assert database.chunk_embeddings.count_documents({}) == 2 * len(chunks)


def test_embedding_after_summary_can_finish_document_readiness(database):
    from backend.services.summary_service.models import summary_profile_id

    identifier, chunks = prepare(database)
    database.documents.update_one(
        {"_id": ObjectId(identifier)},
        {
            "$set": {
                "summary_status": "COMPLETED",
                "active_summary_id": "synthetic-summary",
                "summary_chunk_set_id": chunks[0].chunk_set_id,
                "summary_parse_run_id": chunks[0].parse_run_id,
                "summary_profile_id": summary_profile_id(SETTINGS),
            }
        },
    )
    with patch(PROVIDER, side_effect=vectors):
        embed_stored_document(database, identifier, SETTINGS)
    assert database.documents.find_one({"_id": ObjectId(identifier)})["status"] == "READY"
