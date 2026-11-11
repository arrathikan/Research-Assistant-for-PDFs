"""Real MongoDB job scheduling and outbox checks; provider/broker boundaries mocked."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from backend.gateway.documents import get_database
from backend.gateway.main import app
from backend.services.jobs.dispatch import dispatch_due, reconcile_requests
from backend.services.jobs.store import (
    JobConflict,
    ensure_job_indexes,
    ensure_requested,
    now,
    read_status,
    retry_job,
)
from backend.shared.broker import BrokerUnavailable
from backend.shared.config import Settings
from backend.shared.job_models import job_id
from backend.tests.test_chunking_integration import database as mongo_database
from backend.tests.test_chunking_integration import seed_parse
from bson import ObjectId
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration
SETTINGS = Settings(_env_file=None)


@pytest.fixture
def database():
    yield from mongo_database.__wrapped__()


def scheduled(database):
    identifier = seed_parse(database)
    ensure_job_indexes(database)
    ensure_requested(database, identifier, SETTINGS)
    return identifier


def test_duplicate_scheduling_has_one_durable_job_and_no_broker_calls(database):
    identifier = scheduled(database)
    first = ensure_requested(database, identifier, SETTINGS)
    assert ensure_requested(database, identifier, SETTINGS) == first
    assert database.processing_jobs.count_documents({}) == 1
    assert first.status == "QUEUED" and first.attempt == 1
    document = database.documents.find_one({"_id": ObjectId(identifier)})
    assert document["processing_requested"]


def test_publisher_failure_leaves_action_pending_then_confirms_it(database):
    identifier = scheduled(database)
    with patch("backend.services.jobs.dispatch.publish", side_effect=BrokerUnavailable()):
        with pytest.raises(BrokerUnavailable):
            dispatch_due(database, MagicMock(), SETTINGS)
    assert database.processing_jobs.find_one({})["dispatch_status"] == "PENDING"
    with patch("backend.services.jobs.dispatch.publish") as publisher:
        assert dispatch_due(database, MagicMock(), SETTINGS) == 1
        assert publisher.call_args.args[1].document_id == identifier
        assert dispatch_due(database, MagicMock(), SETTINGS) == 0


def test_fast_consumer_cannot_have_its_next_action_marked_as_sent(database):
    identifier = scheduled(database)

    def consumed(*_):
        database.processing_jobs.update_one(
            {"_id": job_id(identifier)},
            {"$set": {"stage": "summary", "dispatch_status": "PENDING"}},
        )

    with patch("backend.services.jobs.dispatch.publish", side_effect=consumed):
        dispatch_due(database, MagicMock(), SETTINGS)
    assert database.processing_jobs.find_one({})["dispatch_status"] == "PENDING"


def test_retry_wait_is_not_published_early_and_terminal_failure_routes_to_dlq(database):
    identifier = scheduled(database)
    database.processing_jobs.update_one(
        {"_id": job_id(identifier)},
        {"$set": {"status": "RETRY_WAIT", "next_attempt_at": now() + timedelta(hours=1)}},
    )
    with patch("backend.services.jobs.dispatch.publish") as publisher:
        assert dispatch_due(database, MagicMock(), SETTINGS) == 0
        publisher.assert_not_called()
    database.processing_jobs.update_one(
        {"_id": job_id(identifier)},
        {
            "$set": {
                "status": "DEAD_LETTER",
                "error_code": "EMBEDDING_FAILED",
                "next_attempt_at": now(),
            }
        },
    )
    with patch("backend.services.jobs.dispatch.publish") as publisher:
        assert dispatch_due(database, MagicMock(), SETTINGS) == 1
        assert publisher.call_args.args[1].reason == "EMBEDDING_FAILED"


def test_manual_retry_increments_generation_and_interrupted_work_requires_review(database):
    identifier = scheduled(database)
    database.processing_jobs.update_one(
        {"_id": job_id(identifier)},
        {"$set": {"status": "DEAD_LETTER", "error_code": "SUMMARY_FAILED"}},
    )
    retried = retry_job(database, identifier, SETTINGS)
    assert retried.generation == 2 and retried.attempt == 1
    assert retry_job(database, identifier, SETTINGS) == retried
    database.processing_jobs.update_one(
        {"_id": job_id(identifier)},
        {"$set": {"status": "DEAD_LETTER", "error_code": "WORKER_INTERRUPTED"}},
    )
    with pytest.raises(JobConflict):
        retry_job(database, identifier, SETTINGS)


def test_ready_documents_and_unrequested_legacy_documents_are_not_scheduled(database):
    identifier = seed_parse(database)
    reconcile_requests(database, SETTINGS)
    assert read_status(database, identifier).status == "NOT_SCHEDULED"
    database.documents.update_one({"_id": ObjectId(identifier)}, {"$set": {"status": "READY"}})
    assert ensure_requested(database, identifier, SETTINGS).status == "NOT_SCHEDULED"
    assert database.processing_jobs.count_documents({}) == 0


def test_requested_upload_is_reconciled_without_touching_other_documents(database):
    wanted, legacy = seed_parse(database), seed_parse(database)
    database.documents.update_one(
        {"_id": ObjectId(wanted)}, {"$set": {"processing_requested": True}}
    )
    reconcile_requests(database, SETTINGS)
    assert read_status(database, wanted).status == "QUEUED"
    assert read_status(database, legacy).status == "NOT_SCHEDULED"


def test_status_api_excludes_worker_tokens_and_retry_is_explicit(database):
    identifier = scheduled(database)
    database.processing_jobs.update_one(
        {"_id": job_id(identifier)},
        {
            "$set": {
                "claim_token": "private-token",
                "status": "DEAD_LETTER",
                "error_code": "SUMMARY_FAILED",
            }
        },
    )
    app.dependency_overrides[get_database] = lambda: database
    try:
        with TestClient(app) as client:
            path = f"/api/v1/documents/{identifier}/processing"
            response = client.get(path)
            assert response.status_code == 200 and "private-token" not in response.text
            assert response.json()["status"] == "DEAD_LETTER"
            assert client.post(path + "/retry").json()["generation"] == 2
            assert client.get("/api/v1/documents/not-an-id/processing").status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_reconciliation_advances_past_already_scheduled_uploads(database):
    identifier = scheduled(database)
    document = database.documents.find_one({"_id": ObjectId(identifier)})
    assert document["processing_scheduled_job_id"] == job_id(identifier)
    # Existing requested uploads must not occupy every reconciliation batch forever.
    assert (
        database.documents.count_documents(
            {"processing_requested": True, "processing_scheduled_job_id": {"$exists": False}}
        )
        == 0
    )
    missing = seed_parse(database)
    database.documents.update_one(
        {"_id": ObjectId(missing)}, {"$set": {"processing_requested": True}}
    )
    reconcile_requests(database, SETTINGS)
    assert read_status(database, missing).status == "QUEUED"
    assert (
        database.documents.count_documents(
            {"processing_requested": True, "processing_scheduled_job_id": {"$exists": False}}
        )
        == 0
    )
