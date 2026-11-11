"""Immutable summary runs and conditional publication for a source generation."""

import json
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4

from backend.services.document_processor.chunk_models import DocumentChunk
from backend.services.document_processor.chunk_storage import ChunkingNotReady, read_document_chunks
from backend.services.summary_service.models import (
    TEXT_FIELDS,
    UNAVAILABLE,
    SummaryError,
    SummaryResult,
    public_summary,
    summary_profile_id,
    validate_draft,
)
from backend.services.summary_service.workflow import Completion, generate_summary
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable
from backend.shared.storage import DocumentNotFound
from bson import ObjectId
from pydantic import ValidationError
from pymongo import ReturnDocument
from pymongo.database import Database
from pymongo.errors import PyMongoError


class SummaryNotReady(LookupError):
    """No summary has been published for the current sources/configuration."""


class SummaryConflict(SummaryError):
    """Another job owns the document or the source generation changed."""


def _now() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(microsecond=now.microsecond // 1000 * 1000)


def _identifier(document_id: str) -> ObjectId:
    if not ObjectId.is_valid(document_id):
        raise ValueError("Invalid document identifier")
    return ObjectId(document_id)


def _validated_result(
    raw: dict[str, Any], chunks: list[DocumentChunk], settings: Settings
) -> SummaryResult:
    try:
        if not isinstance(raw, dict) or not raw.get("generated_at"):
            raise ValueError("Missing generation timestamp")
        result = SummaryResult.model_validate(raw)
        fields = {}
        for field in (*TEXT_FIELDS, "authors"):
            sources = [
                source.model_dump(exclude={"field"})
                for source in result.sources
                if source.field == field
            ]
            if field == "authors":
                fields[field] = {"names": result.authors, "sources": sources}
            else:
                missing = field in result.unavailable_fields
                if missing and getattr(result, field) != UNAVAILABLE:
                    raise ValueError("Inconsistent missing field")
                fields[field] = {
                    "text": None if missing else getattr(result, field),
                    "sources": sources,
                }
        draft = validate_draft(json.dumps(fields), chunks)
        expected = public_summary(draft, chunks, settings).model_copy(
            update={"generated_at": result.generated_at}
        )
        if expected != result:
            raise ValueError("Summary metadata mismatch")
        return result
    except (ValidationError, SummaryError, ValueError, TypeError):
        raise StorageUnavailable(
            "Saved summary validation failed; reconciliation required"
        ) from None


def read_summary(
    database: Database[dict[str, Any]], document_id: str, settings: Settings
) -> SummaryResult:
    identifier = _identifier(document_id)
    profile = summary_profile_id(settings)
    try:
        document = database.documents.find_one({"_id": identifier})
        if document is None:
            raise DocumentNotFound("Document not found")
        if document.get("summary_status") == "FAILED":
            raise SummaryError("Summary generation failed; retry the summary job")
        if (
            document.get("summary_status") != "COMPLETED"
            or not document.get("active_summary_id")
            or document.get("summary_profile_id") != profile
            or document.get("summary_chunk_set_id") != document.get("active_chunk_set_id")
            or document.get("summary_parse_run_id") != document.get("active_parse_run_id")
        ):
            raise SummaryNotReady("Summary is not complete for the current document and model")
        try:
            chunks = read_document_chunks(database, str(identifier))
        except ChunkingNotReady:
            raise SummaryNotReady("Current parsed chunks are not ready") from None
        record = database.summary_runs.find_one(
            {
                "_id": document["active_summary_id"],
                "document_id": str(identifier),
                "chunk_set_id": chunks[0].chunk_set_id,
                "parse_run_id": chunks[0].parse_run_id,
                "summary_profile_id": profile,
            }
        )
        if record is None:
            raise StorageUnavailable("Published summary record is missing")
        result = _validated_result(record.get("result", {}), chunks, settings)
        if not database.documents.find_one(
            {
                "_id": identifier,
                "active_summary_id": record["_id"],
                "summary_status": "COMPLETED",
                "active_chunk_set_id": chunks[0].chunk_set_id,
                "active_parse_run_id": chunks[0].parse_run_id,
            }
        ):
            raise SummaryNotReady("Document changed while reading its summary")
        return result
    except PyMongoError:
        raise StorageUnavailable("Summary retrieval unavailable") from None


def summarize_stored_document(
    database: Database[dict[str, Any]],
    document_id: str,
    settings: Settings,
    complete: Completion | None = None,
) -> SummaryResult:
    identifier = _identifier(document_id)
    document_id = str(identifier)
    profile = summary_profile_id(settings)
    try:
        document = database.documents.find_one({"_id": identifier})
        if document is None:
            raise DocumentNotFound("Document not found")
        if document.get("chunking_status") != "COMPLETED":
            raise SummaryNotReady("Complete parsing and chunking before generating a summary")
        chunks = read_document_chunks(database, document_id)
        chunk_set, parse_run = chunks[0].chunk_set_id, chunks[0].parse_run_id
        if (
            document.get("active_chunk_set_id") != chunk_set
            or document.get("active_parse_run_id") != parse_run
        ):
            raise SummaryConflict("Summary source generation changed")
        if (
            document.get("summary_status") == "COMPLETED"
            and document.get("summary_profile_id") == profile
            and document.get("summary_chunk_set_id") == chunk_set
        ):
            return read_summary(database, document_id, settings)
        summary_id = sha256(f"{document_id}:{chunk_set}:{profile}".encode()).hexdigest()
        cached = database.summary_runs.find_one({"_id": summary_id})
        cached_result = (
            _validated_result(cached.get("result", {}), chunks, settings) if cached else None
        )
        if (
            cached_result is None
            and complete is None
            and (
                not settings.openrouter_api_key.strip()
                or settings.openrouter_api_key.startswith("your_")
            )
        ):
            raise SummaryError("OPENROUTER_API_KEY is required to generate a summary")
        database.summary_runs.create_index(
            [("document_id", 1), ("chunk_set_id", 1), ("summary_profile_id", 1)],
            unique=True,
            name="document_chunk_summary_profile",
        )
        attempt = uuid4().hex
        claim = database.documents.find_one_and_update(
            {
                "_id": identifier,
                "active_chunk_set_id": chunk_set,
                "active_parse_run_id": parse_run,
                "chunking_status": "COMPLETED",
                "summary_status": {"$ne": "RUNNING"},
                "status": {"$in": ["PENDING", "FAILED", "READY"]},
            },
            {
                "$set": {
                    "summary_status": "RUNNING",
                    "summary_run_id": attempt,
                    "status": "SUMMARIZING",
                    "error_message": None,
                    "updated_at": _now(),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if claim is None:
            raise SummaryConflict("Document is already processing or its source generation changed")
    except PyMongoError:
        raise StorageUnavailable("Summary initialization unavailable") from None

    def publish(result: SummaryResult) -> None:
        _validated_result(result.model_dump(), chunks, settings)
        database.summary_runs.update_one(
            {"_id": summary_id},
            {
                "$setOnInsert": {
                    "document_id": document_id,
                    "chunk_set_id": chunk_set,
                    "parse_run_id": parse_run,
                    "summary_profile_id": profile,
                    "result": result.model_dump(),
                    "created_at": _now(),
                }
            },
            upsert=True,
        )
        # A summary can be produced without Atlas. Whole-document READY also needs
        # completed embeddings for these chunks and the configured embedding model.
        embedding = claim.get("embedding_profile") or {}
        ready = (
            claim.get("embedding_status") == "COMPLETED"
            and claim.get("embedded_chunk_set_id") == chunk_set
            and embedding.get("model") == settings.voyage_model
            and embedding.get("dimensions") == settings.voyage_dimensions
        )
        result_update = database.documents.update_one(
            {
                "_id": identifier,
                "active_chunk_set_id": chunk_set,
                "active_parse_run_id": parse_run,
                "summary_run_id": attempt,
                "status": "SUMMARIZING",
            },
            {
                "$set": {
                    "active_summary_id": summary_id,
                    "summary_profile_id": profile,
                    "summary_chunk_set_id": chunk_set,
                    "summary_parse_run_id": parse_run,
                    "summary_status": "COMPLETED",
                    "summarized_at": _now(),
                    "updated_at": _now(),
                    "status": "READY" if ready else "PENDING",
                    "error_message": None,
                },
                "$unset": {"summary_run_id": ""},
            },
        )
        if result_update.matched_count != 1:
            raise SummaryConflict(
                "Summary source generation or ownership changed before publication"
            )

    try:
        if cached_result is not None:
            publish(cached_result)
        else:
            generate_summary(chunks, settings, complete=complete, save=publish)
        return read_summary(database, document_id, settings)
    except Exception:
        try:
            database.documents.update_one(
                {
                    "_id": identifier,
                    "active_chunk_set_id": chunk_set,
                    "active_parse_run_id": parse_run,
                    "summary_run_id": attempt,
                },
                {
                    "$set": {
                        "summary_status": "FAILED",
                        "status": "FAILED",
                        "updated_at": _now(),
                        "error_message": "Summary generation failed; check model/storage configuration and retry",
                    },
                    "$unset": {"summary_run_id": ""},
                },
            )
        except PyMongoError:
            raise StorageUnavailable(
                "Summary failed and failure status could not be saved"
            ) from None
        raise SummaryError(
            "Summary generation failed; check model/storage configuration and retry"
        ) from None
