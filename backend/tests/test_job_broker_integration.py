"""Real RabbitMQ + MongoDB + HTTP upload/status; only paid providers are simulated."""

import os
import time
from contextlib import contextmanager
from io import BytesIO
from threading import Event, Thread
from unittest.mock import patch
from uuid import uuid4

import pika
import pytest
from backend.gateway.documents import get_database
from backend.gateway.main import app
from backend.services.document_processor.normalization import normalize_parsed_pages
from backend.services.jobs.processor import process_message
from backend.services.jobs.runtime import dispatcher_loop, worker_loop
from backend.services.jobs.store import envelope, read_status
from backend.shared.broker import connect_broker, publish
from backend.shared.config import Settings
from backend.shared.embedding_models import EmbeddingError
from backend.shared.job_models import DeadLetter, job_id
from backend.tests.test_chunking_integration import database as mongo_database
from backend.tests.test_embedding_integration import vectors
from backend.tests.test_summary_workflow import context_completion
from fastapi.testclient import TestClient
from pypdf import PdfWriter

pytestmark = pytest.mark.integration


@pytest.fixture
def broker_database():
    if not os.environ.get("RESEARCHAI_TEST_RABBITMQ_URL"):
        pytest.skip("Set RESEARCHAI_TEST_RABBITMQ_URL for isolated real broker checks")
    yield from mongo_database.__wrapped__()


@pytest.fixture
def settings(broker_database):
    prefix = "researchai_test_" + uuid4().hex
    host, port = broker_database.client.address
    return Settings(
        _env_file=None,
        mongodb_uri=f"mongodb://{host}:{port}",
        mongodb_db_name=broker_database.name,
        rabbitmq_url=os.environ["RESEARCHAI_TEST_RABBITMQ_URL"],
        ingestion_queue=prefix + "_ingest",
        summary_queue=prefix + "_summary",
        dlq_queue=prefix + "_dlq",
        job_poll_seconds=0.1,
        job_retry_base_seconds=1,
        job_retry_max_seconds=1,
        job_max_attempts=2,
        job_heartbeat_seconds=1,
        job_lease_seconds=30,
        llama_cloud_api_key="synthetic-parser",
        voyage_api_key="synthetic-vectors",
        openrouter_api_key="synthetic-completion",
    )


def wait_until(predicate, seconds=25):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError("Isolated broker workflow did not reach its expected state")


@contextmanager
def workers(settings):
    stop = Event()
    threads = [
        Thread(target=dispatcher_loop, args=(settings, stop)),
        Thread(target=worker_loop, args=(settings, "ingestion", stop)),
        Thread(target=worker_loop, args=(settings, "summary", stop)),
    ]
    try:
        for thread in threads:
            thread.start()
        yield
    finally:
        stop.set()
        for thread in threads:
            thread.join(timeout=15)
        assert not any(thread.is_alive() for thread in threads)
        with connect_broker(settings) as (_, channel):
            for queue in (settings.ingestion_queue, settings.summary_queue, settings.dlq_queue):
                channel.queue_delete(queue=queue)


def upload(client):
    writer, content = PdfWriter(), BytesIO()
    writer.add_blank_page(width=200, height=300)
    writer.add_metadata({"/Title": "Synthetic broker verification " + uuid4().hex})
    writer.write(content)
    response = client.post(
        "/api/v1/documents",
        files={"file": ("synthetic.pdf", content.getvalue(), "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()["document"]["id"]


def parsed(identifier, *_):
    return normalize_parsed_pages(
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


@contextmanager
def api_client(database, settings):
    app.dependency_overrides[get_database] = lambda: database
    try:
        with (
            patch("backend.gateway.documents.get_settings", return_value=settings),
            patch("backend.gateway.processing.get_settings", return_value=settings),
            TestClient(app) as client,
        ):
            yield client
    finally:
        app.dependency_overrides.clear()


def test_real_queue_flow_retries_reuses_outputs_ignores_duplicates_and_sanitizes_poison(
    broker_database, settings
):
    database = broker_database
    failures = 0

    def embedding(texts, config):
        nonlocal failures
        failures += 1
        if failures == 1:
            raise EmbeddingError("synthetic transient failure")
        return vectors(texts, config)

    with api_client(database, settings) as client:
        identifier = upload(client)
        first = envelope(database.processing_jobs.find_one({"_id": job_id(identifier)}))
        with (
            patch(
                "backend.services.document_processor.extraction.parse_with_llamaparse",
                side_effect=parsed,
            ) as parser,
            patch(
                "backend.services.document_processor.embedding_storage.embed_documents",
                side_effect=embedding,
            ) as embed,
            patch(
                "backend.shared.openrouter.OpenRouterClient.complete",
                side_effect=context_completion,
            ) as summary,
            patch(
                "backend.services.jobs.runtime.process_message", wraps=process_message
            ) as process,
        ):
            with workers(settings):
                wait_until(lambda: read_status(database, identifier).status == "COMPLETED")
                assert client.get(f"/api/v1/documents/{identifier}").json()["status"] == "READY"
                assert parser.call_count == 1 and embed.call_count == 2 and summary.call_count == 1
                with connect_broker(settings) as (_, channel):
                    publish(channel, first, settings)
                    publish(channel, first, settings)
                    channel.basic_publish(
                        exchange="",
                        routing_key=settings.ingestion_queue,
                        body=b'{"secret":"must-not-copy"}',
                        mandatory=True,
                        properties=pika.BasicProperties(delivery_mode=2),
                    )
                    wait_until(
                        lambda: process.call_count >= 5
                    )  # Failed ingestion, retry, summary, two duplicates.

                    def dead_letter():
                        method, properties, body = channel.basic_get(
                            queue=settings.dlq_queue, auto_ack=False
                        )
                        if method:
                            channel.basic_ack(delivery_tag=method.delivery_tag)
                            return body
                        return None

                    body = wait_until(dead_letter)
                    assert DeadLetter.model_validate_json(body).reason == "INVALID_MESSAGE"
                    assert b"must-not-copy" not in body
                assert parser.call_count == 1 and embed.call_count == 2 and summary.call_count == 1


def test_real_dead_letter_is_published_and_explicit_retry_resumes_cached_stages(
    broker_database, settings
):
    from backend.services.summary_service.models import SummaryError

    database = broker_database
    with api_client(database, settings) as client:
        identifier = upload(client)
        with (
            patch(
                "backend.services.document_processor.extraction.parse_with_llamaparse",
                side_effect=parsed,
            ) as parser,
            patch(
                "backend.services.document_processor.embedding_storage.embed_documents",
                side_effect=vectors,
            ) as embed,
            patch(
                "backend.shared.openrouter.OpenRouterClient.complete",
                side_effect=SummaryError("synthetic failure"),
            ) as summary,
        ):
            with workers(settings):
                wait_until(lambda: read_status(database, identifier).status == "DEAD_LETTER")
                assert summary.call_count == settings.job_max_attempts
                wait_until(
                    lambda: (
                        database.processing_jobs.find_one({"_id": job_id(identifier)})[
                            "dispatch_status"
                        ]
                        == "PUBLISHED"
                    )
                )
                with connect_broker(settings) as (_, channel):
                    method, _, body = channel.basic_get(queue=settings.dlq_queue, auto_ack=False)
                    assert method is not None
                    dead = DeadLetter.model_validate_json(body)
                    assert dead.reason == "SUMMARY_FAILED" and dead.job.document_id == identifier
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                parser_calls, embedding_calls = parser.call_count, embed.call_count
                summary.side_effect = context_completion
                response = client.post(f"/api/v1/documents/{identifier}/processing/retry")
                assert response.status_code == 200 and response.json()["generation"] == 2
                wait_until(lambda: read_status(database, identifier).status == "COMPLETED")
                assert parser.call_count == parser_calls and embed.call_count == embedding_calls
                assert client.get(f"/api/v1/documents/{identifier}").json()["status"] == "READY"
