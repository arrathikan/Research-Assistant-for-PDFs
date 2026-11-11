"""Versioned chunk embeddings and reusable content vectors in MongoDB."""

from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
from typing import Any, Literal
from uuid import uuid4

from backend.services.document_processor.chunk_models import DocumentChunk
from backend.services.document_processor.chunk_storage import read_document_chunks
from backend.services.summary_service.models import summary_profile_id
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable
from backend.shared.embedding_models import EmbeddingError, EmbeddingProfile, validate_vectors
from backend.shared.models import ChunkingStatus, DocumentStatus, EmbeddingStatus
from backend.shared.storage import DocumentNotFound
from backend.shared.voyage import document_batches, embed_documents, embedding_profile
from bson import ObjectId
from pydantic import BaseModel
from pymongo import ReturnDocument, UpdateOne
from pymongo.database import Database
from pymongo.errors import PyMongoError


class EmbeddingNotReady(LookupError):
    """No completed embeddings cover the current parsed chunk set/profile."""


class EmbeddingConflict(RuntimeError):
    """Embedding ownership or source generation changed."""


class EmbeddingSummary(BaseModel):
    document_id: str
    chunk_set_id: str
    embedding_profile_id: str
    model: str
    dimensions: int
    chunk_count: int
    embedded_at: datetime
    status: Literal["COMPLETED"] = "COMPLETED"


def _now() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(microsecond=now.microsecond // 1000 * 1000)


def _hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _vector_id(profile_id: str, content_hash: str) -> str:
    return _hash(profile_id + ":" + content_hash)


def ensure_embedding_indexes(database: Database[dict[str, Any]]) -> None:
    try:
        database.embedding_vectors.create_index(
            [("embedding_profile_id", 1), ("content_sha256", 1)],
            unique=True,
            name="profile_content_vector",
        )
        database.chunk_embeddings.create_index(
            [("document_id", 1), ("chunk_set_id", 1), ("embedding_profile_id", 1), ("chunk_id", 1)],
            unique=True,
            name="chunk_profile_embedding",
        )
    except PyMongoError:
        raise StorageUnavailable("Embedding indexes unavailable") from None


def _load_vectors(
    database: Database[dict[str, Any]], wanted: dict[str, str], profile: EmbeddingProfile
) -> dict[str, list[float]]:
    vectors = {}
    for record in database.embedding_vectors.find({"_id": {"$in": list(wanted)}}):
        identifier = record.get("_id")
        if (
            identifier not in wanted
            or record.get("embedding_profile_id") != profile.id
            or record.get("content_sha256") != wanted[identifier]
        ):
            raise StorageUnavailable("Cached embedding metadata does not match its content/profile")
        try:
            vectors[identifier] = validate_vectors(
                [record.get("embedding")], 1, profile.dimensions
            )[0]
        except EmbeddingError:
            raise StorageUnavailable(
                "Cached embedding vector is invalid; reconciliation required"
            ) from None
    return vectors


def read_embedding_summary(
    database: Database[dict[str, Any]], document_id: str, settings: Settings
) -> EmbeddingSummary:
    if not ObjectId.is_valid(document_id):
        raise ValueError("Invalid document identifier")
    profile = embedding_profile(settings)
    try:
        document = database.documents.find_one({"_id": ObjectId(document_id)})
        if document is None:
            raise DocumentNotFound("Document not found")
        if (
            document.get("embedding_status") != EmbeddingStatus.COMPLETED
            or document.get("active_embedding_profile_id") != profile.id
            or not document.get("active_chunk_set_id")
            or document.get("embedded_chunk_set_id") != document.get("active_chunk_set_id")
            or document.get("chunked_parse_run_id") != document.get("active_parse_run_id")
        ):
            raise EmbeddingNotReady(
                "Complete embeddings for the current chunks and configured model first"
            )
        query = {
            "document_id": str(document["_id"]),
            "chunk_set_id": document["active_chunk_set_id"],
            "embedding_profile_id": profile.id,
        }
        count = database.chunk_embeddings.count_documents(query)
        if (
            count != document.get("embedding_count")
            or count != document.get("chunk_count")
            or count <= 0
        ):
            raise StorageUnavailable("Published embedding coverage is incomplete")
        return EmbeddingSummary(
            document_id=str(document["_id"]),
            chunk_set_id=document["active_chunk_set_id"],
            embedding_profile_id=profile.id,
            model=profile.model,
            dimensions=profile.dimensions,
            chunk_count=count,
            embedded_at=document["embedded_at"],
        )
    except PyMongoError:
        raise StorageUnavailable("Embedding metadata retrieval unavailable") from None


def save_embeddings(
    database: Database[dict[str, Any]],
    chunks: list[DocumentChunk],
    vectors_by_content_hash: dict[str, list[float]],
    profile: EmbeddingProfile,
) -> None:
    """Persist searchable snapshots without mutating source chunks or publishing."""
    if not chunks:
        return
    document_id, chunk_set, parse_run = (
        chunks[0].document_id,
        chunks[0].chunk_set_id,
        chunks[0].parse_run_id,
    )
    operations = []
    for chunk in chunks:
        if (chunk.document_id, chunk.chunk_set_id, chunk.parse_run_id) != (
            document_id,
            chunk_set,
            parse_run,
        ):
            raise EmbeddingError("Embedding chunks must belong to one document generation")
        digest = _hash(chunk.content)
        vector = validate_vectors([vectors_by_content_hash.get(digest)], 1, profile.dimensions)[0]
        record = {
            "_id": _vector_id(profile.id, chunk.id),
            "document_id": document_id,
            "chunk_set_id": chunk_set,
            "parse_run_id": parse_run,
            "chunk_id": chunk.id,
            "embedding_profile_id": profile.id,
            "model": profile.model,
            "dimensions": profile.dimensions,
            "content_sha256": digest,
            "embedding": vector,
            "chunk": chunk.model_dump(by_alias=False),
            "sdk_version": version("voyageai"),
            "created_at": _now(),
        }
        operations.append(UpdateOne({"_id": record["_id"]}, {"$setOnInsert": record}, upsert=True))
    database.chunk_embeddings.bulk_write(operations, ordered=True)
    scope = {
        "document_id": document_id,
        "chunk_set_id": chunk_set,
        "embedding_profile_id": profile.id,
    }
    if database.chunk_embeddings.count_documents(scope) != len(chunks):
        raise StorageUnavailable("Embedding snapshot coverage is incomplete")


def embed_stored_document(
    database: Database[dict[str, Any]], document_id: str, settings: Settings
) -> EmbeddingSummary:
    """Embed only missing content, then publish complete chunk/profile coverage.

    Cache vectors contain no source text. Search snapshots retain scoped chunk
    text/source metadata independently from the immutable chunk collection.
    """
    if not ObjectId.is_valid(document_id):
        raise ValueError("Invalid document identifier")
    identifier = ObjectId(document_id)
    document_id = str(identifier)
    profile = embedding_profile(settings)
    try:
        document = database.documents.find_one({"_id": identifier})
        if document is None:
            raise DocumentNotFound("Document not found")
        if document.get("chunking_status") != ChunkingStatus.COMPLETED:
            raise EmbeddingNotReady("Complete chunking before creating embeddings")
        chunks = read_document_chunks(database, document_id)
        chunk_set = chunks[0].chunk_set_id
        parse_run = chunks[0].parse_run_id
        if (
            document.get("active_chunk_set_id") != chunk_set
            or document.get("active_parse_run_id") != parse_run
        ):
            raise EmbeddingConflict("Chunk or parsed generation changed")
        if (
            document.get("embedding_status") == EmbeddingStatus.COMPLETED
            and document.get("active_embedding_profile_id") == profile.id
            and document.get("embedded_chunk_set_id") == chunk_set
        ):
            return read_embedding_summary(database, document_id, settings)
        texts = {_hash(chunk.content): chunk.content for chunk in chunks}
        wanted = {_vector_id(profile.id, digest): digest for digest in texts}
        cached = _load_vectors(database, wanted, profile)
        missing = [
            text for digest, text in texts.items() if _vector_id(profile.id, digest) not in cached
        ]
        batches = list(document_batches(missing, settings))
        if batches and (
            not settings.voyage_api_key.strip() or settings.voyage_api_key.startswith("your_")
        ):
            raise EmbeddingError("VOYAGE_API_KEY is required for uncached chunk content")
        ensure_embedding_indexes(database)
        attempt = uuid4().hex
        claim = database.documents.find_one_and_update(
            {
                "_id": identifier,
                "active_chunk_set_id": chunk_set,
                "active_parse_run_id": parse_run,
                "chunking_status": ChunkingStatus.COMPLETED,
                "embedding_status": {"$ne": EmbeddingStatus.RUNNING},
                "status": {
                    "$in": [DocumentStatus.PENDING, DocumentStatus.FAILED, DocumentStatus.READY]
                },
            },
            {
                "$set": {
                    "embedding_status": EmbeddingStatus.RUNNING,
                    "embedding_run_id": attempt,
                    "status": DocumentStatus.EMBEDDING,
                    "updated_at": _now(),
                    "error_message": None,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if claim is None:
            raise EmbeddingConflict(
                "Document is already processing or its source generation changed"
            )
    except PyMongoError:
        raise StorageUnavailable("Embedding initialization unavailable") from None
    try:
        for batch in batches:
            vectors = embed_documents(batch, settings)
            for text, vector in zip(batch, vectors, strict=True):
                digest = _hash(text)
                database.embedding_vectors.update_one(
                    {"_id": _vector_id(profile.id, digest)},
                    {
                        "$setOnInsert": {
                            "embedding_profile_id": profile.id,
                            "content_sha256": digest,
                            "model": profile.model,
                            "dimensions": profile.dimensions,
                            "embedding": vector,
                            "sdk_version": version("voyageai"),
                            "created_at": _now(),
                        }
                    },
                    upsert=True,
                )
        cached = _load_vectors(database, wanted, profile)
        if len(cached) != len(wanted):
            raise StorageUnavailable("Embedding cache did not retain all requested content")
        save_embeddings(
            database,
            chunks,
            {digest: cached[_vector_id(profile.id, digest)] for digest in texts},
            profile,
        )
        summary_ready = (
            bool(claim.get("active_summary_id"))
            and claim.get("summary_status") == "COMPLETED"
            and claim.get("summary_chunk_set_id") == chunk_set
            and claim.get("summary_parse_run_id") == parse_run
            and claim.get("summary_profile_id") == summary_profile_id(settings)
        )
        result = database.documents.update_one(
            {
                "_id": identifier,
                "active_chunk_set_id": chunk_set,
                "active_parse_run_id": parse_run,
                "embedding_run_id": attempt,
                "status": DocumentStatus.EMBEDDING,
            },
            {
                "$set": {
                    "embedding_status": EmbeddingStatus.COMPLETED,
                    "active_embedding_profile_id": profile.id,
                    "embedding_profile": profile.model_dump(),
                    "embedded_chunk_set_id": chunk_set,
                    "embedding_count": len(chunks),
                    "embedded_at": _now(),
                    "status": DocumentStatus.READY if summary_ready else DocumentStatus.PENDING,
                    "updated_at": _now(),
                    "error_message": None,
                },
                "$unset": {"embedding_run_id": ""},
            },
        )
        if result.matched_count != 1:
            raise EmbeddingConflict(
                "Embedding ownership or source generation changed before publication"
            )
        return read_embedding_summary(database, document_id, settings)
    except Exception:
        try:
            database.documents.update_one(
                {"_id": identifier, "active_chunk_set_id": chunk_set, "embedding_run_id": attempt},
                {
                    "$set": {
                        "embedding_status": EmbeddingStatus.FAILED,
                        "status": DocumentStatus.FAILED,
                        "updated_at": _now(),
                        "error_message": "Document embedding failed; check provider/storage configuration and retry",
                    },
                    "$unset": {"embedding_run_id": ""},
                },
            )
        except PyMongoError:
            raise StorageUnavailable(
                "Embedding failed and failure status could not be saved"
            ) from None
        raise EmbeddingError(
            "Document embedding failed; check provider/storage configuration and retry"
        ) from None
