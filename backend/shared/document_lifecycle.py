"""Short document write guards and retryable, document-scoped permanent cleanup.

Provider requests run outside the guard. Deletion marks metadata before cleaning;
late provider results must acquire the same guard before writing derived records.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from time import monotonic, sleep
from typing import Any
from uuid import uuid4

from backend.shared.database import StorageUnavailable
from backend.shared.storage import DocumentNotFound
from bson import ObjectId
from gridfs import GridFSBucket, NoFile
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, PyMongoError, WriteConcernError

DOCUMENT_COLLECTIONS = (
    "parsed_pages",
    "source_elements",
    "chunks",
    "chunk_embeddings",
    "summary_runs",
    "summaries",
    "chat_conversations",
    "chat_turns",
    "chat_messages",
    "processing_jobs",
)


class DocumentBusy(StorageUnavailable):
    """A short write or an uncertain previous write prevents safe deletion."""


@contextmanager
def document_write(
    database: Database[dict[str, Any]], document_id: str, *, wait_seconds: float = 5
) -> Iterator[None]:
    """Serialize derived writes against deletion without holding a lock over AI calls.

    An ambiguous database failure retains the token: never expire it while a
    server write might still finish. An operator can reconcile it after stopping
    the writer. Normal success and non-storage validation failures release it.
    """
    identifier, token = ObjectId(document_id), uuid4().hex
    try:
        deadline = monotonic() + wait_seconds
        while True:
            result = database.documents.update_one(
                {
                    "_id": identifier,
                    "deletion_state": {"$exists": False},
                    "document_write_token": {"$exists": False},
                },
                {"$set": {"document_write_token": token}},
            )
            if result.matched_count == 1:
                break
            record = database.documents.find_one({"_id": identifier})
            if record is None or record.get("deletion_state") == "DELETING":
                raise DocumentNotFound("Document is unavailable")
            if monotonic() >= deadline:
                raise DocumentBusy("Document data is being saved; retry shortly")
            sleep(0.02)
    except PyMongoError:
        raise StorageUnavailable("Document write ownership is uncertain") from None
    uncertain = False
    try:
        yield
    except PyMongoError as error:
        details = getattr(error, "details", None) or {}
        uncertain = (
            isinstance(error, (ConnectionFailure, WriteConcernError))
            or error.timeout
            or bool(details.get("writeConcernErrors") or details.get("writeConcernError"))
        )
        raise
    finally:
        if not uncertain:
            try:
                database.documents.update_one(
                    {"_id": identifier, "document_write_token": token},
                    {"$unset": {"document_write_token": ""}},
                )
            except PyMongoError:
                raise StorageUnavailable("Document write ownership needs review") from None


def delete_document(database: Database[dict[str, Any]], document_id: str) -> None:
    """Return only after cleanup; retain DELETING metadata on partial failure.

    Repeating cleanup, including concurrent requests, is safe: all removals use
    this exact ID, and the barrier denies new derived writes. Shared content-vector
    cache entries and global indexes are deliberately retained.
    """
    identifier = ObjectId(document_id)
    document_id = str(identifier)
    try:
        record = database.documents.find_one({"_id": identifier})
        if record is not None:
            marked = database.documents.update_one(
                {"_id": identifier, "document_write_token": {"$exists": False}},
                {"$set": {"deletion_state": "DELETING"}},
            )
            if marked.matched_count != 1:
                raise DocumentBusy("Document data is being saved; retry shortly")
        files = database["fs.files"]
        file_ids = {
            item["_id"]
            for item in files.find({"metadata.document_id": {"$in": [document_id, identifier]}})
        }
        if record and record.get("gridfs_file_id"):
            file_ids.add(ObjectId(str(record["gridfs_file_id"])))
        bucket = GridFSBucket(database)
        for file_id in file_ids:
            if database.documents.find_one(
                {"_id": {"$ne": identifier}, "gridfs_file_id": {"$in": [file_id, str(file_id)]}}
            ):
                continue  # Never remove a file referenced by a different document.
            stored = files.find_one({"_id": file_id})
            owner = (stored.get("metadata") or {}).get("document_id") if stored else None
            if owner is not None and str(owner) != document_id:
                raise StorageUnavailable("Original file ownership requires review")
            try:
                bucket.delete(file_id)  # Also removes fs.chunks, even after a partial prior delete.
            except NoFile:
                pass
        for name in DOCUMENT_COLLECTIONS:
            database[name].delete_many({"document_id": {"$in": [document_id, identifier]}})
        database.documents.delete_one({"_id": identifier, "deletion_state": "DELETING"})
        if database.documents.find_one({"_id": identifier}) is not None:
            raise StorageUnavailable("Document cleanup did not finish")
    except PyMongoError:
        raise StorageUnavailable("Document deletion did not finish; retry deletion") from None
