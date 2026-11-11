"""Real disposable MongoDB summary lifecycle; all completion calls are synthetic."""

from unittest.mock import Mock

import pytest
from backend.services.document_processor.chunk_storage import chunk_stored_document
from backend.services.summary_service.models import SummaryError
from backend.services.summary_service.storage import (
    SummaryConflict,
    SummaryNotReady,
    read_summary,
    summarize_stored_document,
)
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable
from backend.tests.test_chunking_integration import database as mongo_database
from backend.tests.test_chunking_integration import seed_parse
from backend.tests.test_summary_workflow import context_completion
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import OperationFailure

pytestmark = pytest.mark.integration
SETTINGS = Settings(_env_file=None)


@pytest.fixture
def database():
    yield from mongo_database.__wrapped__()


def prepare(database, embedded=True):
    identifier = seed_parse(database)
    chunks = chunk_stored_document(database, identifier, SETTINGS)
    if embedded:
        database.documents.update_one(
            {"_id": ObjectId(identifier)},
            {
                "$set": {
                    "embedding_status": "COMPLETED",
                    "embedded_chunk_set_id": chunks[0].chunk_set_id,
                    "embedding_profile": {
                        "model": SETTINGS.voyage_model,
                        "dimensions": SETTINGS.voyage_dimensions,
                    },
                }
            },
        )
    return identifier


def test_summary_persists_round_trips_and_reuses_without_paid_calls(database):
    identifier = prepare(database)
    complete = Mock(side_effect=context_completion)
    result = summarize_stored_document(database, identifier, SETTINGS, complete)
    assert read_summary(database, identifier, SETTINGS) == result
    assert summarize_stored_document(database, identifier, SETTINGS, complete) == result
    complete.assert_called_once()
    assert database.summary_runs.count_documents({}) == 1
    document = database.documents.find_one({"_id": ObjectId(identifier)})
    assert document["status"] == "READY" and document["summary_status"] == "COMPLETED"
    assert "summary_run_id" not in document


def test_summary_can_be_read_before_embeddings_without_claiming_document_ready(database):
    identifier = prepare(database, embedded=False)
    summarize_stored_document(database, identifier, SETTINGS, context_completion)
    assert read_summary(database, identifier, SETTINGS).sources
    assert database.documents.find_one({"_id": ObjectId(identifier)})["status"] == "PENDING"


def test_schema_failure_does_not_publish_and_marks_safe_failure(database):
    identifier = prepare(database)
    complete = Mock(return_value="private malformed output")
    with pytest.raises(SummaryError):
        summarize_stored_document(database, identifier, SETTINGS, complete)
    document = database.documents.find_one({"_id": ObjectId(identifier)})
    assert document["status"] == "FAILED" and document["summary_status"] == "FAILED"
    assert "active_summary_id" not in document
    assert "private" not in document["error_message"]
    assert database.summary_runs.count_documents({}) == 0
    assert complete.call_count == 3


def test_running_claim_blocks_another_job_before_completion(database):
    identifier = prepare(database)
    database.documents.update_one(
        {"_id": ObjectId(identifier)},
        {"$set": {"summary_status": "RUNNING", "status": "SUMMARIZING"}},
    )
    complete = Mock()
    with pytest.raises(SummaryConflict):
        summarize_stored_document(database, identifier, SETTINGS, complete)
    complete.assert_not_called()


def test_changed_source_cannot_publish_stale_results(database):
    identifier = prepare(database)

    def change_source(*args):
        database.documents.update_one(
            {"_id": ObjectId(identifier)}, {"$set": {"active_parse_run_id": "different-parse"}}
        )
        return context_completion(*args)

    with pytest.raises(SummaryError):
        summarize_stored_document(database, identifier, SETTINGS, change_source)
    assert "active_summary_id" not in database.documents.find_one({"_id": ObjectId(identifier)})
    with pytest.raises(SummaryNotReady):
        read_summary(database, identifier, SETTINGS)


def test_persisted_result_survives_publication_failure_and_retry_uses_it(database, monkeypatch):
    identifier = prepare(database)
    original = Collection.update_one

    def fail_publication(collection, query, update, *args, **kwargs):
        if (
            collection.name == "documents"
            and update.get("$set", {}).get("summary_status") == "COMPLETED"
        ):
            raise OperationFailure("private database detail")
        return original(collection, query, update, *args, **kwargs)

    with monkeypatch.context() as context:
        context.setattr(Collection, "update_one", fail_publication)
        with pytest.raises(SummaryError):
            summarize_stored_document(database, identifier, SETTINGS, context_completion)
    assert database.summary_runs.count_documents({}) == 1
    complete = Mock()
    assert summarize_stored_document(database, identifier, SETTINGS, complete).sources
    complete.assert_not_called()


def test_model_change_keeps_previous_immutable_summary(database):
    identifier = prepare(database)
    first = summarize_stored_document(database, identifier, SETTINGS, context_completion)
    changed = SETTINGS.model_copy(
        update={"primary_reasoning_model": "meta-llama/llama-3.3-70b-instruct"}
    )
    with pytest.raises(SummaryNotReady):
        read_summary(database, identifier, changed)
    second = summarize_stored_document(database, identifier, changed, context_completion)
    assert first.summary_profile_id != second.summary_profile_id
    assert database.summary_runs.count_documents({}) == 2


def test_saved_evidence_is_revalidated_on_read(database):
    identifier = prepare(database)
    summarize_stored_document(database, identifier, SETTINGS, context_completion)
    database.summary_runs.update_one(
        {"document_id": identifier}, {"$set": {"result.sources.0.page_number": 99}}
    )
    with pytest.raises(StorageUnavailable, match="validation failed"):
        read_summary(database, identifier, SETTINGS)
