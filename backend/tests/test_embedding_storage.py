"""Embedding publication and reuse boundaries with mocked Mongo/provider calls."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from backend.services.document_processor.chunking import chunk_document
from backend.services.document_processor.embedding_storage import (
    EmbeddingConflict,
    EmbeddingNotReady,
    EmbeddingSummary,
    _hash,
    _vector_id,
    embed_stored_document,
    read_embedding_summary,
)
from backend.services.document_processor.parsed_models import ParsedDocument, ParsedPage
from backend.shared.config import Settings
from backend.shared.embedding_models import EmbeddingError
from backend.shared.voyage import embedding_profile
from bson import ObjectId

ID = "507f1f77bcf86cd799439011"
SETTINGS = Settings(_env_file=None, voyage_api_key="test-only-key")


def chunks():
    return chunk_document(
        ParsedDocument(
            document_id=ID,
            pages=[ParsedPage(document_id=ID, page_number=1, markdown="## Method\n\nEvidence")],
        ),
        "parse-a",
    )


def metadata(**values):
    return {
        "_id": ObjectId(ID),
        "active_chunk_set_id": chunks()[0].chunk_set_id,
        "active_parse_run_id": "parse-a",
        "chunked_parse_run_id": "parse-a",
        "chunking_status": "COMPLETED",
        "chunk_count": len(chunks()),
        "status": "PENDING",
        **values,
    }


def summary():
    profile = embedding_profile(SETTINGS)
    return EmbeddingSummary(
        document_id=ID,
        chunk_set_id=chunks()[0].chunk_set_id,
        embedding_profile_id=profile.id,
        model=profile.model,
        dimensions=profile.dimensions,
        chunk_count=len(chunks()),
        embedded_at=datetime.now(timezone.utc),
    )


def cached():
    profile = embedding_profile(SETTINGS)
    return {_vector_id(profile.id, _hash(chunk.content)): [0.1] * 1024 for chunk in chunks()}


def test_missing_vectors_are_stored_before_conditional_publication():
    db = MagicMock()
    db.documents.find_one.return_value = metadata()
    db.chunk_embeddings.count_documents.return_value = len(chunks())
    db.documents.update_one.return_value.matched_count = 1
    done = summary()
    with (
        patch(
            "backend.services.document_processor.embedding_storage.read_document_chunks",
            return_value=chunks(),
        ),
        patch(
            "backend.services.document_processor.embedding_storage._load_vectors",
            side_effect=[{}, cached()],
        ),
        patch(
            "backend.services.document_processor.embedding_storage.embed_documents",
            return_value=[[0.1] * 1024 for _ in chunks()],
        ) as provider,
        patch(
            "backend.services.document_processor.embedding_storage.read_embedding_summary",
            return_value=done,
        ),
    ):
        assert embed_stored_document(db, ID, SETTINGS) == done
    provider.assert_called_once()
    db.chunk_embeddings.bulk_write.assert_called_once()
    published = db.documents.update_one.call_args.args
    assert published[0]["active_chunk_set_id"] == chunks()[0].chunk_set_id
    assert published[1]["$set"]["embedding_status"] == "COMPLETED"
    assert published[1]["$set"]["status"] == "PENDING"


def test_completed_profile_reuses_published_coverage_without_provider_call():
    db = MagicMock()
    db.documents.find_one.return_value = metadata(
        embedding_status="COMPLETED",
        active_embedding_profile_id=embedding_profile(SETTINGS).id,
        embedded_chunk_set_id=chunks()[0].chunk_set_id,
    )
    with (
        patch(
            "backend.services.document_processor.embedding_storage.read_document_chunks",
            return_value=chunks(),
        ),
        patch(
            "backend.services.document_processor.embedding_storage.read_embedding_summary",
            return_value=summary(),
        ),
        patch("backend.services.document_processor.embedding_storage.embed_documents") as provider,
    ):
        embed_stored_document(db, ID, SETTINGS)
        provider.assert_not_called()
    db.documents.find_one_and_update.assert_not_called()


def test_missing_key_leaves_uncached_document_unchanged():
    db = MagicMock()
    db.documents.find_one.return_value = metadata()
    with (
        patch(
            "backend.services.document_processor.embedding_storage.read_document_chunks",
            return_value=chunks(),
        ),
        patch(
            "backend.services.document_processor.embedding_storage._load_vectors", return_value={}
        ),
    ):
        with pytest.raises(EmbeddingError, match="required"):
            embed_stored_document(db, ID, Settings(_env_file=None, voyage_api_key=""))
    db.documents.find_one_and_update.assert_not_called()


def test_running_claim_blocks_provider():
    db = MagicMock()
    db.documents.find_one.return_value = metadata()
    db.documents.find_one_and_update.return_value = None
    with (
        patch(
            "backend.services.document_processor.embedding_storage.read_document_chunks",
            return_value=chunks(),
        ),
        patch(
            "backend.services.document_processor.embedding_storage._load_vectors", return_value={}
        ),
        patch("backend.services.document_processor.embedding_storage.embed_documents") as provider,
    ):
        with pytest.raises(EmbeddingConflict):
            embed_stored_document(db, ID, SETTINGS)
        provider.assert_not_called()


def test_provider_failure_does_not_publish_partial_coverage():
    db = MagicMock()
    db.documents.find_one.return_value = metadata()
    with (
        patch(
            "backend.services.document_processor.embedding_storage.read_document_chunks",
            return_value=chunks(),
        ),
        patch(
            "backend.services.document_processor.embedding_storage._load_vectors", return_value={}
        ),
        patch(
            "backend.services.document_processor.embedding_storage.embed_documents",
            side_effect=RuntimeError("secret-provider-detail"),
        ),
    ):
        with pytest.raises(EmbeddingError):
            embed_stored_document(db, ID, SETTINGS)
    update = db.documents.update_one.call_args.args[1]["$set"]
    assert update["embedding_status"] == "FAILED" and "secret" not in update["error_message"]
    assert "active_embedding_profile_id" not in update
    db.chunk_embeddings.bulk_write.assert_not_called()


def test_summary_checks_current_chunk_and_embedding_profiles():
    db = MagicMock()
    profile = embedding_profile(SETTINGS)
    db.documents.find_one.return_value = metadata(
        embedding_status="COMPLETED",
        active_embedding_profile_id=profile.id,
        embedded_chunk_set_id=chunks()[0].chunk_set_id,
        embedding_count=len(chunks()),
        embedded_at=datetime.now(timezone.utc),
    )
    db.chunk_embeddings.count_documents.return_value = len(chunks())
    assert read_embedding_summary(db, ID, SETTINGS).model == "voyage-3"
    db.documents.find_one.return_value["active_chunk_set_id"] = "changed"
    with pytest.raises(EmbeddingNotReady):
        read_embedding_summary(db, ID, SETTINGS)
