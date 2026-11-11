"""Confirm pending job publications, then conditionally mark that exact action sent."""

from backend.services.jobs.store import ensure_requested, envelope, now, storage_operation
from backend.shared.broker import publish
from backend.shared.config import Settings
from backend.shared.job_models import DeadLetter
from pika.adapters.blocking_connection import BlockingChannel
from pymongo.database import Database


def reconcile_requests(database: Database, settings: Settings) -> None:
    # Only repair uploads that explicitly requested processing, never arbitrary legacy PDFs.
    with storage_operation():
        records = database.documents.find(
            {"processing_requested": True, "status": {"$ne": "READY"}}, {"_id": 1}
        ).limit(100)
        for document in records:
            ensure_requested(database, str(document["_id"]), settings)


def dispatch_due(database: Database, channel: BlockingChannel, settings: Settings) -> int:
    sent = 0
    with storage_operation():
        records = (
            database.processing_jobs.find(
                {
                    "dispatch_status": "PENDING",
                    "next_attempt_at": {"$lte": now()},
                    "status": {"$in": ["QUEUED", "RETRY_WAIT", "DEAD_LETTER"]},
                }
            )
            .sort("next_attempt_at", 1)
            .limit(100)
        )
        for record in records:
            message = envelope(record)
            payload = (
                DeadLetter(reason=record["error_code"], job=message)
                if record["status"] == "DEAD_LETTER"
                else message
            )
            publish(channel, payload, settings)
            # A very fast consumer may already have advanced to a different action.
            database.processing_jobs.update_one(
                {
                    "_id": record["_id"],
                    **message.identity(),
                    "status": record["status"],
                    "dispatch_status": "PENDING",
                },
                {"$set": {"dispatch_status": "PUBLISHED", "published_at": now()}},
            )
            sent += 1
    return sent
