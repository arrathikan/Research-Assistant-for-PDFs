"""Broker contract checks independent of any running broker or provider."""

from unittest.mock import MagicMock, patch

import pytest
from backend.shared.broker import BrokerUnavailable, connect_broker, declare_queues, publish
from backend.shared.config import Settings
from backend.shared.job_models import DeadLetter, JobMessage, job_id
from pika.exceptions import UnroutableError
from pydantic import ValidationError

ID = "507f1f77bcf86cd799439011"
SETTINGS = Settings(_env_file=None)


def message(**updates):
    return JobMessage(job_id=job_id(ID), document_id=ID, **updates)


def test_minimal_message_roundtrip_and_stable_identity():
    original = message()
    assert JobMessage.model_validate_json(original.model_dump_json()) == original
    assert original.message_id() != message(attempt=2).message_id()
    assert "text" not in original.model_dump()


@pytest.mark.parametrize(
    "updates",
    [
        {"job_id": "f" * 64},
        {"document_id": "other"},
        {"stage": "chat"},
        {"attempt": 0},
        {"attempt": 6},
        {"attempt": True},
        {"generation": 0},
        {"schema_version": 2},
        {"credentials": "not-allowed"},
    ],
)
def test_invalid_or_extended_envelopes_are_rejected(updates):
    with pytest.raises(ValidationError):
        JobMessage.model_validate({**message().model_dump(), **updates})


def test_queues_are_durable_with_confirms():
    channel = MagicMock()
    declare_queues(channel, SETTINGS)
    assert channel.queue_declare.call_count == 3
    assert all(call.kwargs["durable"] for call in channel.queue_declare.call_args_list)
    channel.confirm_delivery.assert_called_once()


@pytest.mark.parametrize("stage", ["ingestion", "summary"])
def test_job_publish_is_persistent_mandatory_and_document_scoped(stage):
    channel = MagicMock()
    job = message(stage=stage)
    publish(channel, job, SETTINGS)
    call = channel.basic_publish.call_args.kwargs
    assert call["mandatory"] and call["properties"].delivery_mode == 2
    assert call["routing_key"] == getattr(SETTINGS, f"{stage}_queue")
    assert JobMessage.model_validate_json(call["body"]) == job


def test_dead_letters_do_not_contain_untrusted_error_details():
    channel = MagicMock()
    publish(channel, DeadLetter(reason="INVALID_MESSAGE"), SETTINGS)
    call = channel.basic_publish.call_args.kwargs
    assert call["routing_key"] == SETTINGS.dlq_queue
    assert b"INVALID_MESSAGE" in call["body"]


def test_unconfirmed_publication_and_bad_connection_are_safe():
    channel = MagicMock()
    channel.basic_publish.side_effect = UnroutableError([])
    with pytest.raises(BrokerUnavailable, match="not confirmed"):
        publish(channel, message(), SETTINGS)
    with patch("backend.shared.broker.pika.BlockingConnection", side_effect=ValueError("secret")):
        with pytest.raises(BrokerUnavailable) as failure:
            with connect_broker(SETTINGS):
                pass
    assert "secret" not in str(failure.value)


@pytest.mark.parametrize(
    "changes",
    [
        {"ingestion_queue": "same", "summary_queue": "same"},
        {"dlq_queue": "amq.reserved"},
        {"job_max_attempts": 6},
        {"job_retry_base_seconds": 5, "job_retry_max_seconds": 1},
        {"job_lease_seconds": 30, "job_heartbeat_seconds": 30},
    ],
)
def test_invalid_job_settings_fail_early(changes):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **changes)
