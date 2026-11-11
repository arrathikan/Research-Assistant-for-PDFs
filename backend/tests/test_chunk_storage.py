"""Chunk generation publication and compatibility guards with mocked storage."""

from unittest.mock import MagicMock, patch

import pytest
from backend.services.document_processor.chunk_models import ChunkingError
from backend.services.document_processor.chunk_storage import (
    ChunkingConflict,
    ChunkingNotReady,
    chunk_stored_document,
    read_document_chunks,
)
from backend.services.document_processor.chunking import chunk_document
from backend.services.document_processor.parsed_models import ParsedDocument, ParsedPage
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable, ensure_chunk_indexes
from backend.shared.storage import DocumentNotFound
from bson import ObjectId
from pymongo.errors import OperationFailure

ID = "507f1f77bcf86cd799439011"
CONFIG = Settings(_env_file=None)


def parsed():
    return ParsedDocument(
        document_id=ID,
        pages=[ParsedPage(document_id=ID, page_number=1, markdown="## Method\n\nEvidence")],
    )


def metadata(**values):
    return {
        "_id": ObjectId(ID),
        "active_parse_run_id": "parse-a",
        "parsing_status": "COMPLETED",
        "status": "PENDING",
        **values,
    }


def test_chunk_generation_writes_then_conditionally_publishes():
    db = MagicMock()
    db.documents.find_one.return_value = metadata()
    db.documents.update_one.return_value.matched_count = 1
    chunks = chunk_document(parsed(), "parse-a")
    with (
        patch(
            "backend.services.document_processor.chunk_storage.read_parsed_document",
            return_value=parsed(),
        ),
        patch(
            "backend.services.document_processor.chunk_storage.read_document_chunks",
            return_value=chunks,
        ),
    ):
        assert chunk_stored_document(db, ID, CONFIG) == chunks
    db.chunks.bulk_write.assert_called_once()
    committed = db.documents.update_one.call_args.args
    assert committed[0]["active_parse_run_id"] == "parse-a"
    assert committed[1]["$set"]["chunking_status"] == "COMPLETED"
    assert committed[1]["$set"]["status"] == "PENDING"
    assert committed[1]["$set"]["active_chunk_set_id"] == chunks[0].chunk_set_id


def test_repeated_chunk_generation_does_not_write_or_claim():
    db = MagicMock()
    chunks = chunk_document(parsed(), "parse-a")
    db.documents.find_one.return_value = metadata(
        active_chunk_set_id=chunks[0].chunk_set_id, chunking_status="COMPLETED"
    )
    with (
        patch(
            "backend.services.document_processor.chunk_storage.read_parsed_document",
            return_value=parsed(),
        ),
        patch(
            "backend.services.document_processor.chunk_storage.read_document_chunks",
            return_value=chunks,
        ),
    ):
        assert chunk_stored_document(db, ID, CONFIG) == chunks
    db.chunks.bulk_write.assert_not_called()
    db.documents.find_one_and_update.assert_not_called()


def test_missing_parse_and_unknown_document():
    db = MagicMock()
    db.documents.find_one.return_value = {"_id": ObjectId(ID)}
    with pytest.raises(ChunkingNotReady):
        chunk_stored_document(db, ID, CONFIG)
    db.documents.find_one.return_value = None
    with pytest.raises(DocumentNotFound):
        chunk_stored_document(db, ID, CONFIG)


def test_existing_claim_prevents_writes():
    db = MagicMock()
    db.documents.find_one.return_value = metadata()
    db.documents.find_one_and_update.return_value = None
    with patch(
        "backend.services.document_processor.chunk_storage.read_parsed_document",
        return_value=parsed(),
    ):
        with pytest.raises(ChunkingConflict):
            chunk_stored_document(db, ID, CONFIG)
    db.chunks.bulk_write.assert_not_called()


def test_failed_chunk_write_is_not_published():
    db = MagicMock()
    db.documents.find_one.return_value = metadata()
    db.chunks.bulk_write.side_effect = OperationFailure("private-db-details")
    with patch(
        "backend.services.document_processor.chunk_storage.read_parsed_document",
        return_value=parsed(),
    ):
        with pytest.raises(ChunkingError):
            chunk_stored_document(db, ID, CONFIG)
    update = db.documents.update_one.call_args.args[1]["$set"]
    assert update["chunking_status"] == "FAILED"
    assert "private" not in update["error_message"]
    assert "active_chunk_set_id" not in update


def test_reader_filters_current_chunk_set_and_provenance():
    db = MagicMock()
    chunks = chunk_document(parsed(), "parse-a")
    db.documents.find_one.return_value = metadata(
        active_chunk_set_id=chunks[0].chunk_set_id,
        chunked_parse_run_id="parse-a",
        chunk_count=len(chunks),
    )
    db.chunks.find.return_value.sort.return_value = [
        chunk.model_dump(by_alias=True) for chunk in chunks
    ]
    assert read_document_chunks(db, ID) == chunks
    db.chunks.find.assert_called_once_with(
        {"document_id": ID, "chunk_set_id": chunks[0].chunk_set_id}
    )


def test_reader_rejects_stale_or_incomplete_sets():
    db = MagicMock()
    db.documents.find_one.return_value = metadata(
        active_chunk_set_id="old-set", chunked_parse_run_id="old-parse"
    )
    with pytest.raises(ChunkingNotReady):
        read_document_chunks(db, ID)
    db.documents.find_one.return_value = metadata(
        active_chunk_set_id="current-set", chunked_parse_run_id="parse-a", chunk_count=1
    )
    db.chunks.find.return_value.sort.return_value = []
    with pytest.raises(StorageUnavailable):
        read_document_chunks(db, ID)


def test_empty_legacy_index_is_migrated_without_deleting_records():
    db = MagicMock()
    db.chunks.index_information.return_value = {
        "document_chunk_index": {"key": [("document_id", 1), ("chunk_index", 1)], "unique": True}
    }
    db.chunks.count_documents.return_value = 0
    ensure_chunk_indexes(db)
    db.chunks.drop_index.assert_called_once_with("document_chunk_index")
    db.chunks.delete_many.assert_not_called()


def test_populated_legacy_index_requires_review_before_migration():
    db = MagicMock()
    db.chunks.index_information.return_value = {
        "document_chunk_index": {"key": [("document_id", 1), ("chunk_index", 1)], "unique": True}
    }
    db.chunks.count_documents.return_value = 1
    with pytest.raises(StorageUnavailable, match="reviewed migration"):
        ensure_chunk_indexes(db)
    db.chunks.drop_index.assert_not_called()
