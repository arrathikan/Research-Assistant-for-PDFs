"""PDF persistence helpers; HTTP validation and processing belong to later stages."""

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from backend.shared.database import StorageUnavailable
from backend.shared.models import DocumentMetadata
from bson import ObjectId
from gridfs import GridFSBucket, NoFile
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError


class StoredDocument(DocumentMetadata):
    """A persisted document has validated, nonoptional storage identifiers."""

    id: str = Field(alias="_id", pattern=r"^[0-9a-f]{24}$")
    gridfs_file_id: str = Field(pattern=r"^[0-9a-f]{24}$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    filename: str = Field(min_length=1)
    file_size_bytes: int = Field(gt=0)
    page_count: int | None = Field(default=None, gt=0)

    model_config = ConfigDict(populate_by_name=True, validate_default=True)

    @field_validator("created_at", "updated_at")
    @classmethod
    def mongo_timestamp(cls, value: datetime) -> datetime:
        """Return the same UTC millisecond precision stored by BSON dates."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        value = value.astimezone(timezone.utc)
        return value.replace(microsecond=(value.microsecond // 1000) * 1000)


class StoredPdfResult(BaseModel):
    document: StoredDocument
    is_duplicate: bool


class DocumentNotFound(LookupError):
    """The document or its original file is missing."""


def _object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise ValueError("Invalid document or file identifier")
    return ObjectId(value)


def _document(record: dict[str, Any]) -> StoredDocument:
    """Convert BSON IDs once at the persistence boundary."""
    data = dict(record)
    data["_id"] = str(data["_id"])
    data["gridfs_file_id"] = str(data["gridfs_file_id"])
    return StoredDocument.model_validate(data)


def get_document(database: Database[dict[str, Any]], document_id: str) -> StoredDocument | None:
    identifier = _object_id(document_id)
    try:
        record = database.documents.find_one({"_id": identifier})
        return _document(record) if record is not None else None
    except PyMongoError:
        raise StorageUnavailable("Document lookup unavailable") from None


def find_document_by_hash(database: Database[dict[str, Any]], digest: str) -> StoredDocument | None:
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("Invalid SHA-256 digest")
    try:
        record = database.documents.find_one({"sha256": digest})
        return _document(record) if record is not None else None
    except PyMongoError:
        raise StorageUnavailable("Document lookup unavailable") from None


def _delete_candidate(bucket: GridFSBucket, file_id: ObjectId) -> None:
    """Delete only this attempt's file; never the deduplication winner's file."""
    try:
        bucket.delete(file_id)
    except NoFile:
        pass
    except PyMongoError:
        raise StorageUnavailable("Storage cleanup failed; reconciliation required") from None


def store_pdf(
    database: Database[dict[str, Any]],
    filename: str,
    content: bytes,
    *,
    page_count: int | None = None,
) -> StoredPdfResult:
    """Persist raw bytes and metadata after ensure_indexes() has succeeded.

    The unique SHA-256 index arbitrates races. Each attempt owns a fresh GridFS
    ID; the losing duplicate deletes only its own file. GridFS and metadata are
    not transactional. An ambiguous insert failure retains the file because the
    server may have committed metadata; reconciliation is documented separately.
    File format and upload size validation are the responsibility of Prompt 5.
    """
    document_id, file_id = ObjectId(), ObjectId()
    digest = sha256(content).hexdigest()
    document = StoredDocument(
        id=str(document_id),
        gridfs_file_id=str(file_id),
        sha256=digest,
        filename=filename,
        file_size_bytes=len(content),
        page_count=page_count,
    )
    existing = find_document_by_hash(database, digest)
    if existing is not None:
        return StoredPdfResult(document=existing, is_duplicate=True)

    bucket = GridFSBucket(database)
    try:
        bucket.upload_from_stream_with_id(
            file_id,
            filename,
            content,
            metadata={
                "document_id": str(document_id),
                "sha256": digest,
                "contentType": "application/pdf",
            },
        )
    except PyMongoError:
        _delete_candidate(bucket, file_id)
        raise StorageUnavailable("PDF storage unavailable") from None

    record = document.model_dump(by_alias=True)
    record["_id"] = document_id
    record["gridfs_file_id"] = file_id
    try:
        database.documents.insert_one(record)
    except DuplicateKeyError:
        _delete_candidate(bucket, file_id)
        winner = find_document_by_hash(database, digest)
        if winner is None:
            raise StorageUnavailable("Duplicate document unavailable; retry lookup")
        return StoredPdfResult(document=winner, is_duplicate=True)
    except PyMongoError:
        # An acknowledged connection loss can hide a successful insert. Deleting
        # the file here could corrupt that document. Retain it for reconciliation.
        raise StorageUnavailable(
            "Document persistence uncertain; reconciliation required"
        ) from None
    return StoredPdfResult(document=document, is_duplicate=False)


def read_pdf(database: Database[dict[str, Any]], document_id: str) -> bytes:
    """Retrieve the original by document ID, never by an ambiguous filename."""
    document = get_document(database, document_id)
    if document is None:
        raise DocumentNotFound("Document not found")
    try:
        with GridFSBucket(database).open_download_stream(
            _object_id(document.gridfs_file_id)
        ) as stream:
            return stream.read()
    except NoFile:
        raise DocumentNotFound("Original PDF not found") from None
    except PyMongoError:
        raise StorageUnavailable("PDF retrieval unavailable") from None
