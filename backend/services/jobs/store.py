"""MongoDB job/outbox state; HTTP scheduling never depends on a running broker."""

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Literal

from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable
from backend.shared.job_models import FailureCode, JobMessage, JobStage, JobStatus, job_id
from backend.shared.storage import DocumentNotFound, get_document
from bson import ObjectId
from pydantic import BaseModel, ValidationError
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError


class JobConflict(RuntimeError):
    """Job cannot be retried safely in its current state."""


class ProcessingView(BaseModel):
    document_id: str
    job_id: str | None = None
    status: JobStatus | Literal["NOT_SCHEDULED"] = "NOT_SCHEDULED"
    stage: JobStage | None = None
    step: str | None = None
    generation: int = 0
    attempt: int = 0
    max_attempts: int = 0
    retry_at: datetime | None = None
    error_code: FailureCode | None = None
    requires_review: bool = False


def now() -> datetime:
    value = datetime.now(timezone.utc)
    return value.replace(microsecond=value.microsecond // 1000 * 1000)


@contextmanager
def storage_operation() -> Iterator[None]:
    try:
        yield
    except (PyMongoError, ValidationError):
        raise StorageUnavailable("Processing job storage unavailable") from None


def ensure_job_indexes(database: Database) -> None:
    with storage_operation():
        database.processing_jobs.create_index(
            [("dispatch_status", 1), ("next_attempt_at", 1)], name="job_outbox_due"
        )
        database.processing_jobs.create_index(
            [("status", 1), ("lease_expires_at", 1)], name="job_expired_leases"
        )


def envelope(record: dict) -> JobMessage:
    return JobMessage.model_validate(
        {key: record[key] for key in JobMessage.model_fields if key in record}
    )


def view(record: dict | None, document_id: str) -> ProcessingView:
    if record is None:
        return ProcessingView(document_id=document_id)
    message = envelope(record)
    return ProcessingView(
        document_id=document_id,
        job_id=message.job_id,
        status=record["status"],
        stage=message.stage,
        step=record.get("step"),
        generation=message.generation,
        attempt=message.attempt,
        max_attempts=record["max_attempts"],
        retry_at=record.get("next_attempt_at") if record["status"] == "RETRY_WAIT" else None,
        error_code=record.get("error_code"),
        requires_review=record.get("error_code") in ("WORKER_INTERRUPTED", "SOURCE_BUSY"),
    )


def ensure_requested(database: Database, document_id: str, settings: Settings) -> ProcessingView:
    with storage_operation():
        document = get_document(database, document_id)
        if document is None:
            raise DocumentNotFound("Document not found")
        if document.status == "READY":
            return read_status(database, document_id)
        database.documents.update_one(
            {"_id": ObjectId(document_id)}, {"$set": {"processing_requested": True}}
        )
        message = JobMessage(job_id=job_id(document_id), document_id=document_id)
        stamp = now()
        record = {
            "_id": message.job_id,
            **message.model_dump(),
            "status": "QUEUED",
            "dispatch_status": "PENDING",
            "max_attempts": settings.job_max_attempts,
            "created_at": stamp,
            "updated_at": stamp,
            "next_attempt_at": stamp,
            "error_code": None,
        }
        try:
            database.processing_jobs.update_one(
                {"_id": message.job_id}, {"$setOnInsert": record}, upsert=True
            )
        except DuplicateKeyError:
            pass  # Concurrent duplicate uploads share the deterministic job identity.
        return read_status(database, document_id)


def read_status(database: Database, document_id: str) -> ProcessingView:
    with storage_operation():
        if get_document(database, document_id) is None:
            raise DocumentNotFound("Document not found")
        record = database.processing_jobs.find_one(
            {"_id": job_id(document_id), "document_id": document_id}
        )
        return view(record, document_id)


def retry_job(database: Database, document_id: str, settings: Settings) -> ProcessingView:
    with storage_operation():
        current = read_status(database, document_id)
        if current.requires_review:
            raise JobConflict("Interrupted or externally running work needs operator review")
        if current.status == "NOT_SCHEDULED":
            return ensure_requested(database, document_id, settings)
        if current.status in ("QUEUED", "RETRY_WAIT", "RUNNING"):
            return current
        if current.status != "DEAD_LETTER":
            raise JobConflict("This document has already completed processing")
        stamp = now()
        result = database.processing_jobs.update_one(
            {"_id": current.job_id, "generation": current.generation, "status": "DEAD_LETTER"},
            {
                "$set": {
                    "status": "QUEUED",
                    "dispatch_status": "PENDING",
                    "generation": current.generation + 1,
                    "attempt": 1,
                    "stage": "ingestion",
                    "step": None,
                    "max_attempts": settings.job_max_attempts,
                    "next_attempt_at": stamp,
                    "updated_at": stamp,
                    "error_code": None,
                },
                "$unset": {"claim_token": "", "lease_expires_at": ""},
            },
        )
        if result.matched_count != 1:
            raise JobConflict("Processing job changed; reload its status")
        return read_status(database, document_id)
