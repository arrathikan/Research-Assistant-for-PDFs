"""Atomic job ownership, bounded retries and explicit interrupted-work recovery."""

from datetime import timedelta
from uuid import uuid4

from backend.services.jobs.store import JobConflict, envelope, now, retry_job, storage_operation
from backend.shared.config import Settings
from backend.shared.job_models import FailureCode, JobMessage
from backend.shared.storage import DocumentNotFound
from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.database import Database


class OwnershipLost(RuntimeError):
    """An expired or replaced worker must not advance a processing job."""


def owned(message: JobMessage, token: str) -> dict:
    return {
        "_id": message.job_id,
        **message.identity(),
        "status": "RUNNING",
        "claim_token": token,
        "lease_expires_at": {"$gt": now()},
    }


def claim_job(database: Database, message: JobMessage, settings: Settings) -> dict | None:
    with storage_operation():
        return database.processing_jobs.find_one_and_update(
            {
                "_id": message.job_id,
                **message.identity(),
                "status": {"$in": ["QUEUED", "RETRY_WAIT"]},
                "next_attempt_at": {"$lte": now()},
            },
            {
                "$set": {
                    "status": "RUNNING",
                    "dispatch_status": "PUBLISHED",
                    "claim_token": uuid4().hex,
                    "lease_expires_at": now() + timedelta(seconds=settings.job_lease_seconds),
                    "updated_at": now(),
                    "error_code": None,
                }
            },
            return_document=ReturnDocument.AFTER,
        )


def update_owned(database: Database, message: JobMessage, token: str, update: dict) -> None:
    with storage_operation():
        if database.processing_jobs.update_one(owned(message, token), update).matched_count != 1:
            raise OwnershipLost("Processing job ownership changed")


def heartbeat(database: Database, message: JobMessage, token: str, settings: Settings) -> None:
    update_owned(
        database,
        message,
        token,
        {
            "$set": {
                "lease_expires_at": now() + timedelta(seconds=settings.job_lease_seconds),
                "updated_at": now(),
            }
        },
    )


def set_step(database: Database, message: JobMessage, token: str, step: str) -> None:
    update_owned(database, message, token, {"$set": {"step": step, "updated_at": now()}})


def advance(database: Database, message: JobMessage, token: str, sources: dict) -> None:
    update_owned(
        database,
        message,
        token,
        {
            "$set": {
                "stage": "summary",
                "step": None,
                "attempt": 1,
                "status": "QUEUED",
                "dispatch_status": "PENDING",
                "next_attempt_at": now(),
                "updated_at": now(),
                **sources,
            },
            "$unset": {"claim_token": "", "lease_expires_at": ""},
        },
    )


def complete(database: Database, message: JobMessage, token: str) -> None:
    update_owned(
        database,
        message,
        token,
        {
            "$set": {
                "status": "COMPLETED",
                "dispatch_status": "NONE",
                "step": "complete",
                "updated_at": now(),
                "error_code": None,
            },
            "$unset": {"claim_token": "", "lease_expires_at": ""},
        },
    )


def fail_job(
    database: Database,
    message: JobMessage,
    token: str,
    code: FailureCode,
    settings: Settings,
    retryable: bool = True,
) -> None:
    with storage_operation():
        record = database.processing_jobs.find_one(owned(message, token))
        if record is None:
            raise OwnershipLost("Processing job ownership changed")
        retry = retryable and message.attempt < record["max_attempts"]
        delay = (
            min(
                settings.job_retry_base_seconds * 2 ** (message.attempt - 1),
                settings.job_retry_max_seconds,
            )
            if retry
            else 0
        )
        update_owned(
            database,
            message,
            token,
            {
                "$set": {
                    "status": "RETRY_WAIT" if retry else "DEAD_LETTER",
                    "dispatch_status": "PENDING",
                    "attempt": message.attempt + 1 if retry else message.attempt,
                    "error_code": code,
                    "next_attempt_at": now() + timedelta(seconds=delay),
                    "updated_at": now(),
                },
                "$unset": {"claim_token": "", "lease_expires_at": ""},
            },
        )
        database.documents.update_one(
            {"_id": ObjectId(message.document_id), "processing_claim_token": token},
            {
                "$set": {
                    "status": "FAILED",
                    "error_message": "Processing failed; check the processing job status",
                    "updated_at": now(),
                }
            },
        )


def expire_jobs(database: Database) -> int:
    count = 0
    with storage_operation():
        for record in database.processing_jobs.find(
            {"status": "RUNNING", "lease_expires_at": {"$lte": now()}}
        ).limit(100):
            message = envelope(record)
            changed = database.processing_jobs.update_one(
                {
                    "_id": record["_id"],
                    **message.identity(),
                    "status": "RUNNING",
                    "claim_token": record["claim_token"],
                    "lease_expires_at": {"$lte": now()},
                },
                {
                    "$set": {
                        "status": "DEAD_LETTER",
                        "dispatch_status": "PENDING",
                        "error_code": "WORKER_INTERRUPTED",
                        "next_attempt_at": now(),
                        "updated_at": now(),
                    }
                },
            )
            if changed.matched_count:
                database.documents.update_one(
                    {
                        "_id": ObjectId(message.document_id),
                        "processing_claim_token": record["claim_token"],
                    },
                    {
                        "$set": {
                            "status": "FAILED",
                            "error_message": "Worker interrupted; operator review required",
                            "updated_at": now(),
                        }
                    },
                )
                count += 1
    return count


def recover_interrupted(database: Database, document_id: str, settings: Settings) -> None:
    """Operator-only after stopping the old workers; retain every successful output."""
    from backend.shared.job_models import job_id

    with storage_operation():
        record = database.processing_jobs.find_one(
            {
                "_id": job_id(document_id),
                "document_id": document_id,
                "status": "DEAD_LETTER",
                "error_code": "WORKER_INTERRUPTED",
            }
        )
        if not record or record["lease_expires_at"] > now():
            raise JobConflict("Only an expired interrupted job can be recovered")
        document = database.documents.find_one({"_id": ObjectId(document_id)})
        if document is None:
            raise DocumentNotFound("Document not found")
        token = record["claim_token"]
        if document.get("processing_claim_token") != token:
            raise JobConflict("Document processing ownership changed; review it manually")
        match = {"_id": document["_id"], "processing_claim_token": token}
        fields = {"status": "FAILED", "updated_at": now()}
        unset = {}
        for stage in ("parsing", "chunking", "embedding", "summary"):
            status, run = f"{stage}_status", f"{stage}_run_id"
            if document.get(status) == "RUNNING":
                match[status], match[run] = "RUNNING", document.get(run)
                fields[status], unset[run] = "FAILED", ""
        update = {"$set": fields}
        if unset:
            update["$unset"] = unset
        if database.documents.update_one(match, update).matched_count != 1:
            raise JobConflict("Document changed during recovery; inspect it again")
        changed = database.processing_jobs.update_one(
            {
                "_id": record["_id"],
                "generation": record["generation"],
                "status": "DEAD_LETTER",
                "claim_token": token,
            },
            {"$set": {"error_code": "PROCESSING_FAILED"}},
        )
        if changed.matched_count != 1:
            raise JobConflict("Job changed during recovery")
        retry_job(database, document_id, settings)
