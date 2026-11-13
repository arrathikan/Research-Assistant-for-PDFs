"""Immutable chunk sets with conditional publication and no provider calls."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from backend.services.document_processor.chunk_models import (
    ChunkingConfig,
    ChunkingError,
    DocumentChunk,
)
from backend.services.document_processor.chunking import chunk_document, chunk_set_id
from backend.services.document_processor.extraction import read_parsed_document
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable, ensure_chunk_indexes
from backend.shared.document_lifecycle import document_write
from backend.shared.models import ChunkingStatus, DocumentStatus, ParsingStatus
from backend.shared.storage import DocumentNotFound
from bson import ObjectId
from pymongo import ASCENDING, ReturnDocument, UpdateOne
from pymongo.database import Database
from pymongo.errors import PyMongoError


class ChunkingNotReady(LookupError):
    """No current complete chunk set is available."""


class ChunkingConflict(RuntimeError):
    """Another worker or a changed parse prevents publishing this chunk set."""


def _now() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(microsecond=now.microsecond // 1000 * 1000)


def read_document_chunks(
    database: Database[dict[str, Any]], document_id: str
) -> list[DocumentChunk]:
    if not ObjectId.is_valid(document_id):
        raise ValueError("Invalid document identifier")
    try:
        document = database.documents.find_one({"_id": ObjectId(document_id)})
        if document is None or document.get("deletion_state") == "DELETING":
            raise DocumentNotFound("Document not found")
        identifier = document.get("active_chunk_set_id")
        if not identifier or document.get("chunked_parse_run_id") != document.get(
            "active_parse_run_id"
        ):
            raise ChunkingNotReady("Chunking is not complete for the current parsed document")
        chunks = [
            DocumentChunk.model_validate(record)
            for record in database.chunks.find(
                {
                    "document_id": str(document["_id"]),
                    "chunk_set_id": identifier,
                }
            ).sort("chunk_index", ASCENDING)
        ]
        if (
            not chunks
            or len(chunks) != document.get("chunk_count")
            or [chunk.chunk_index for chunk in chunks] != list(range(len(chunks)))
        ):
            raise StorageUnavailable("Published chunk set is incomplete")
        if any(chunk.parse_run_id != document["active_parse_run_id"] for chunk in chunks):
            raise StorageUnavailable("Published chunk provenance does not match its document")
        return chunks
    except PyMongoError:
        raise StorageUnavailable("Chunk retrieval unavailable") from None


def chunk_stored_document(
    database: Database[dict[str, Any]], document_id: str, settings: Settings
) -> list[DocumentChunk]:
    """Chunk a completed parse; repeated configuration reuses its active output."""
    if not ObjectId.is_valid(document_id):
        raise ValueError("Invalid document identifier")
    identifier = ObjectId(document_id)
    try:
        document = database.documents.find_one({"_id": identifier})
        if document is None or document.get("deletion_state") == "DELETING":
            raise DocumentNotFound("Document not found")
        parse_id = document.get("active_parse_run_id")
        if not parse_id or document.get("parsing_status") != ParsingStatus.COMPLETED:
            raise ChunkingNotReady("Complete document parsing before chunking")
        parsed = read_parsed_document(database, document_id)
        config = ChunkingConfig(
            chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
        )
        target = chunk_set_id(parsed, parse_id, config)
        if (
            document.get("active_chunk_set_id") == target
            and document.get("chunking_status") == ChunkingStatus.COMPLETED
        ):
            return read_document_chunks(database, document_id)
        ensure_chunk_indexes(database)
        attempt = uuid4().hex
        claim = database.documents.find_one_and_update(
            {
                "_id": identifier,
                "deletion_state": {"$exists": False},
                "active_parse_run_id": parse_id,
                "parsing_status": ParsingStatus.COMPLETED,
                "status": {"$in": [DocumentStatus.PENDING, DocumentStatus.FAILED]},
                "chunking_status": {"$ne": ChunkingStatus.RUNNING},
            },
            {
                "$set": {
                    "chunking_status": ChunkingStatus.RUNNING,
                    "chunking_run_id": attempt,
                    "updated_at": _now(),
                    "error_message": None,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if claim is None:
            raise ChunkingConflict("Document is already processing or its parsed version changed")
    except PyMongoError:
        raise StorageUnavailable("Chunking initialization unavailable") from None
    try:
        chunks = chunk_document(parsed, parse_id, config)
        operations = [
            UpdateOne(
                {"_id": chunk.id}, {"$setOnInsert": chunk.model_dump(by_alias=True)}, upsert=True
            )
            for chunk in chunks
        ]
        with document_write(database, document_id):
            database.chunks.bulk_write(operations, ordered=True)
            completed = database.documents.update_one(
                {
                    "_id": identifier,
                    "deletion_state": {"$exists": False},
                    "active_parse_run_id": parse_id,
                    "parsing_status": ParsingStatus.COMPLETED,
                    "chunking_run_id": attempt,
                    "status": {"$in": [DocumentStatus.PENDING, DocumentStatus.FAILED]},
                },
                {
                    "$set": {
                        "active_chunk_set_id": target,
                        "chunked_parse_run_id": parse_id,
                        "chunking_status": ChunkingStatus.COMPLETED,
                        "chunked_at": _now(),
                        "chunk_count": len(chunks),
                        "status": DocumentStatus.PENDING,
                        "updated_at": _now(),
                        "error_message": None,
                    },
                    "$unset": {"chunking_run_id": ""},
                },
            )
            if completed.matched_count != 1:
                raise ChunkingConflict(
                    "Chunking ownership or parsed version changed before publication"
                )
        return read_document_chunks(database, document_id)
    except Exception:
        try:
            database.documents.update_one(
                {"_id": identifier, "active_parse_run_id": parse_id, "chunking_run_id": attempt},
                {
                    "$set": {
                        "chunking_status": ChunkingStatus.FAILED,
                        "status": DocumentStatus.FAILED,
                        "updated_at": _now(),
                        "error_message": "Document chunking failed; check configuration and retry",
                    },
                    "$unset": {"chunking_run_id": ""},
                },
            )
        except PyMongoError:
            raise StorageUnavailable(
                "Chunking failed and failure status could not be saved"
            ) from None
        raise ChunkingError("Document chunking failed; check configuration and retry") from None
