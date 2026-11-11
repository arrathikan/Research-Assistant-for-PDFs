"""Real document lifecycle and job ownership; expensive provider boundaries mocked."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import timedelta
from io import BytesIO
from unittest.mock import Mock, patch

import pytest
from backend.services.document_processor.normalization import normalize_parsed_pages
from backend.services.jobs.lifecycle import (
    OwnershipLost,
    claim_job,
    expire_jobs,
    heartbeat,
    recover_interrupted,
)
from backend.services.jobs.processor import process_message
from backend.services.jobs.store import (
    JobConflict,
    ensure_requested,
    envelope,
    now,
    read_status,
    retry_job,
)
from backend.shared.config import Settings
from backend.shared.embedding_models import EmbeddingError
from backend.shared.job_models import job_id
from backend.shared.storage import get_document, store_pdf
from backend.tests.test_chunking_integration import database as mongo_database
from backend.tests.test_embedding_integration import vectors
from backend.tests.test_summary_workflow import context_completion
from bson import ObjectId
from pypdf import PdfWriter

pytestmark = pytest.mark.integration
SETTINGS = Settings(
    _env_file=None,
    llama_cloud_api_key="synthetic-parser",
    voyage_api_key="synthetic-vector",
    openrouter_api_key="synthetic-completion",
)


@pytest.fixture
def database():
    yield from mongo_database.__wrapped__()


def scheduled(database):
    writer, output = PdfWriter(), BytesIO()
    writer.add_blank_page(width=200, height=300)
    writer.write(output)
    identifier = store_pdf(database, "synthetic.pdf", output.getvalue(), page_count=1).document.id
    ensure_requested(database, identifier, SETTINGS)
    return identifier


def current(database, identifier):
    return envelope(database.processing_jobs.find_one({"_id": job_id(identifier)}))


@contextmanager
def providers(identifier):
    parsed = normalize_parsed_pages(
        identifier,
        [
            {
                "pages": [
                    {
                        "page": 1,
                        "md": "## Method\n\nSynthetic evidence describes a controlled method.",
                    }
                ]
            }
        ],
        1,
    )
    with (
        patch(
            "backend.services.document_processor.extraction.parse_with_llamaparse",
            return_value=parsed,
        ) as parser,
        patch(
            "backend.services.document_processor.embedding_storage.embed_documents",
            side_effect=vectors,
        ) as embedding,
        patch(
            "backend.shared.openrouter.OpenRouterClient.complete", side_effect=context_completion
        ) as summary,
    ):
        yield parser, embedding, summary


def due(database, identifier):
    database.processing_jobs.update_one(
        {"_id": job_id(identifier)}, {"$set": {"next_attempt_at": now()}}
    )
    return current(database, identifier)


def test_full_pipeline_reuses_completed_outputs_and_ignores_duplicate_deliveries(database):
    identifier = scheduled(database)
    first = current(database, identifier)
    with providers(identifier) as (parser, embedding, summary):
        process_message(database, first, SETTINGS)
        queued = read_status(database, identifier)
        assert queued.stage == "summary" and queued.status == "QUEUED"
        second = current(database, identifier)
        process_message(database, second, SETTINGS)
        assert read_status(database, identifier).status == "COMPLETED"
        assert get_document(database, identifier).status == "READY"
        assert parser.call_count == embedding.call_count == summary.call_count == 1
        process_message(database, first, SETTINGS)
        process_message(database, second, SETTINGS)
        assert parser.call_count == embedding.call_count == summary.call_count == 1


def test_retry_resumes_after_parsing_and_does_not_retry_early(database):
    identifier = scheduled(database)
    first = current(database, identifier)
    with providers(identifier) as (parser, embedding, _):
        embedding.side_effect = EmbeddingError("sensitive-provider-text")
        process_message(database, first, SETTINGS)
        waiting = read_status(database, identifier)
        assert waiting.status == "RETRY_WAIT" and waiting.attempt == 2
        assert waiting.error_code == "EMBEDDING_FAILED"
        assert "sensitive-provider-text" not in waiting.model_dump_json()
        process_message(database, current(database, identifier), SETTINGS)
        assert embedding.call_count == 1
        embedding.side_effect = vectors
        process_message(database, due(database, identifier), SETTINGS)
        assert read_status(database, identifier).stage == "summary"
        assert parser.call_count == 1 and embedding.call_count == 2


def test_summary_failures_are_bounded_and_have_a_durable_dead_letter_action(database):
    from backend.services.summary_service.models import SummaryError

    identifier = scheduled(database)
    with providers(identifier) as (_, _, summary):
        process_message(database, current(database, identifier), SETTINGS)
        summary.side_effect = SummaryError("private-secret")
        for _ in range(SETTINGS.job_max_attempts):
            process_message(database, due(database, identifier), SETTINGS)
        record = database.processing_jobs.find_one({"_id": job_id(identifier)})
        assert record["status"] == "DEAD_LETTER" and record["dispatch_status"] == "PENDING"
        assert record["error_code"] == "SUMMARY_FAILED"
        assert summary.call_count == SETTINGS.job_max_attempts
        assert "private-secret" not in str(record)


def test_atomic_claim_allows_only_one_worker(database):
    identifier = scheduled(database)
    message = current(database, identifier)
    with ThreadPoolExecutor(max_workers=4) as executor:
        claims = list(executor.map(lambda _: claim_job(database, message, SETTINGS), range(4)))
    assert sum(item is not None for item in claims) == 1


def test_expired_job_is_reviewed_before_native_claims_can_be_recovered(database):
    identifier = scheduled(database)
    message = current(database, identifier)
    record = claim_job(database, message, SETTINGS)
    heartbeat(database, message, record["claim_token"], SETTINGS)
    with pytest.raises(JobConflict):
        recover_interrupted(database, identifier, SETTINGS)
    database.documents.update_one(
        {"_id": ObjectId(identifier)},
        {
            "$set": {
                "processing_claim_token": record["claim_token"],
                "parsing_status": "RUNNING",
                "parsing_run_id": "interrupted-run",
                "status": "PARSING",
            }
        },
    )
    database.processing_jobs.update_one(
        {"_id": job_id(identifier)}, {"$set": {"lease_expires_at": now() - timedelta(seconds=1)}}
    )
    with pytest.raises(OwnershipLost):
        heartbeat(database, message, record["claim_token"], SETTINGS)
    assert expire_jobs(database) == 1
    assert read_status(database, identifier).requires_review
    with pytest.raises(JobConflict):
        retry_job(database, identifier, SETTINGS)
    recover_interrupted(database, identifier, SETTINGS)
    recovered = read_status(database, identifier)
    assert recovered.status == "QUEUED" and recovered.generation == 2
    document = database.documents.find_one({"_id": ObjectId(identifier)})
    assert document["parsing_status"] == "FAILED" and "parsing_run_id" not in document


def test_unrelated_running_stage_is_never_reset(database):
    identifier = scheduled(database)
    database.documents.update_one(
        {"_id": ObjectId(identifier)},
        {"$set": {"parsing_status": "RUNNING", "parsing_run_id": "unrelated-run"}},
    )
    with providers(identifier) as (parser, _, _):
        process_message(database, current(database, identifier), SETTINGS)
        parser.assert_not_called()
    assert read_status(database, identifier).error_code == "SOURCE_BUSY"
    assert (
        database.documents.find_one({"_id": ObjectId(identifier)})["parsing_run_id"]
        == "unrelated-run"
    )


def test_changed_source_cannot_be_summarized_under_old_job_generation(database):
    identifier = scheduled(database)
    with providers(identifier) as (_, _, summary):
        process_message(database, current(database, identifier), SETTINGS)
        database.documents.update_one(
            {"_id": ObjectId(identifier)}, {"$set": {"active_chunk_set_id": "f" * 64}}
        )
        process_message(database, current(database, identifier), SETTINGS)
        summary.assert_not_called()
    assert read_status(database, identifier).error_code == "SOURCE_CHANGED"


def test_manual_retry_invalidates_old_messages_and_starts_from_ingestion(database):
    identifier = scheduled(database)
    old = current(database, identifier)
    database.processing_jobs.update_one(
        {"_id": job_id(identifier)},
        {"$set": {"status": "DEAD_LETTER", "stage": "summary", "error_code": "SUMMARY_FAILED"}},
    )
    retried = retry_job(database, identifier, SETTINGS)
    assert retried.stage == "ingestion" and retried.generation == 2
    with patch("backend.services.jobs.processor.parse_pdf", Mock()) as parser:
        process_message(database, old, SETTINGS)
        parser.assert_not_called()
