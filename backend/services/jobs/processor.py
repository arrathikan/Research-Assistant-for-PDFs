"""Run existing processing services under a job lease; reuse their immutable outputs."""

from threading import Event, Thread

from backend.services.document_processor.chunk_models import ChunkingError
from backend.services.document_processor.chunk_storage import (
    ChunkingConflict,
    chunk_stored_document,
)
from backend.services.document_processor.embedding_storage import (
    EmbeddingConflict,
    EmbeddingNotReady,
    embed_stored_document,
    read_embedding_summary,
)
from backend.services.document_processor.extraction import ParsingConflict, parse_pdf
from backend.services.document_processor.parsed_models import ParsingError
from backend.services.jobs.lifecycle import (
    OwnershipLost,
    advance,
    claim_job,
    complete,
    fail_job,
    heartbeat,
    set_step,
)
from backend.services.jobs.store import storage_operation
from backend.services.summary_service.models import SummaryError
from backend.services.summary_service.storage import (
    SummaryConflict,
    read_summary,
    summarize_stored_document,
)
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable
from backend.shared.embedding_models import EmbeddingError
from backend.shared.job_models import FailureCode, JobMessage
from backend.shared.storage import DocumentNotFound
from bson import ObjectId
from pymongo.database import Database


class StageFailure(RuntimeError):
    def __init__(self, code: FailureCode, retryable: bool = True):
        self.code, self.retryable = code, retryable
        super().__init__(code)


def _sources(database: Database, message: JobMessage, settings: Settings) -> dict:
    try:
        embedding = read_embedding_summary(database, message.document_id, settings)
    except EmbeddingNotReady:
        raise StageFailure("SOURCE_CHANGED", retryable=False) from None
    with storage_operation():
        document = database.documents.find_one({"_id": ObjectId(message.document_id)})
        if document is None:
            raise DocumentNotFound("Document not found")
        return {
            "source_parse_run_id": document["active_parse_run_id"],
            "source_chunk_set_id": embedding.chunk_set_id,
            "source_embedding_profile_id": embedding.embedding_profile_id,
        }


def _run(
    database: Database, message: JobMessage, record: dict, settings: Settings, lost: Event
) -> None:
    token = record["claim_token"]
    with storage_operation():
        document = database.documents.find_one({"_id": ObjectId(message.document_id)})
        if document is None:
            raise DocumentNotFound("Document not found")
        if any(
            document.get(f"{stage}_status") == "RUNNING"
            for stage in ("parsing", "chunking", "embedding", "summary")
        ):
            raise StageFailure("SOURCE_BUSY", retryable=False)
        match = {
            "_id": document["_id"],
            **{
                f"{stage}_status": {"$ne": "RUNNING"}
                for stage in ("parsing", "chunking", "embedding", "summary")
            },
        }
        if (
            database.documents.update_one(
                match,
                {"$set": {"processing_job_id": message.job_id, "processing_claim_token": token}},
            ).matched_count
            != 1
        ):
            raise StageFailure("SOURCE_BUSY", retryable=False)
    steps = (
        [
            ("parsing", parse_pdf, "PARSING_FAILED"),
            ("chunking", chunk_stored_document, "CHUNKING_FAILED"),
            ("embedding", embed_stored_document, "EMBEDDING_FAILED"),
        ]
        if message.stage == "ingestion"
        else [("summary", summarize_stored_document, "SUMMARY_FAILED")]
    )
    if message.stage == "summary" and _sources(database, message, settings) != {
        key: record.get(key)
        for key in ("source_parse_run_id", "source_chunk_set_id", "source_embedding_profile_id")
    }:
        raise StageFailure("SOURCE_CHANGED", retryable=False)
    for step, operation, code in steps:
        if lost.is_set():
            raise OwnershipLost("Worker lease heartbeat failed")
        set_step(database, message, token, step)
        try:
            operation(database, message.document_id, settings)
        except (ParsingConflict, ChunkingConflict, EmbeddingConflict, SummaryConflict):
            raise StageFailure("SOURCE_BUSY", retryable=False) from None
        except (ParsingError, ChunkingError, EmbeddingError, SummaryError):
            raise StageFailure(code) from None
    if lost.is_set():
        raise OwnershipLost("Worker lease heartbeat failed")
    sources = _sources(database, message, settings)
    if message.stage == "ingestion":
        advance(database, message, token, sources)
    else:
        if sources != {key: record.get(key) for key in sources}:
            raise StageFailure("SOURCE_CHANGED", retryable=False)
        read_summary(database, message.document_id, settings)
        with storage_operation():
            if (
                database.documents.find_one(
                    {"_id": ObjectId(message.document_id), "status": "READY"}
                )
                is None
            ):
                raise StageFailure("SOURCE_CHANGED", retryable=False)
        complete(database, message, token)


def process_message(database: Database, message: JobMessage, settings: Settings) -> None:
    record = claim_job(database, message, settings)
    if record is None:
        return  # Completed, stale, future or duplicate deliveries never invoke providers.
    token = record["claim_token"]
    stop, lost = Event(), Event()

    def renew() -> None:
        while not stop.wait(settings.job_heartbeat_seconds):
            try:
                heartbeat(database, message, token, settings)
            except (StorageUnavailable, OwnershipLost):
                lost.set()
                return

    thread = Thread(target=renew, name="job-lease-heartbeat", daemon=True)
    thread.start()
    try:
        try:
            _run(database, message, record, settings, lost)
        except DocumentNotFound:
            fail_job(database, message, token, "DOCUMENT_MISSING", settings, retryable=False)
        except StageFailure as failure:
            fail_job(database, message, token, failure.code, settings, failure.retryable)
        except StorageUnavailable:
            raise  # Keep delivery unacknowledged; do not claim success without durable state.
        except OwnershipLost:
            raise
        except Exception:
            fail_job(database, message, token, "PROCESSING_FAILED", settings)
    except OwnershipLost:
        return  # The durable job/expired-lease dispatcher owns recovery now.
    finally:
        stop.set()
        thread.join(timeout=settings.mongodb_timeout_ms / 1000 + 1)
