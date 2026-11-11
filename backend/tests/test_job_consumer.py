"""Acknowledgements follow durable results; slow provider work stays off the I/O thread."""

from threading import Event, get_ident
from unittest.mock import MagicMock, patch

import pytest
from backend.services.jobs.runtime import consume_once
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable
from backend.shared.job_models import JobMessage, job_id

SETTINGS = Settings(_env_file=None)
ID = "507f1f77bcf86cd799439011"


@pytest.mark.parametrize("persisted", [True, False])
def test_acknowledgement_only_after_durable_processing_on_another_thread(persisted):
    stop, started = Event(), Event()
    connection, channel, database = MagicMock(), MagicMock(), MagicMock()
    channel.consumer_tags = []
    message = JobMessage(job_id=job_id(ID), document_id=ID)
    method = MagicMock(delivery_tag=7)
    caller = get_ident()

    def processing(*_):
        assert get_ident() != caller
        started.set()
        stop.set()
        if not persisted:
            raise StorageUnavailable("safe failure")

    delivered = False

    def events(**_):
        nonlocal delivered
        if not delivered:
            delivered = True
            channel.basic_consume.call_args.kwargs["on_message_callback"](
                channel, method, None, message.model_dump_json().encode()
            )
        started.wait(1)

    connection.process_data_events.side_effect = events
    with (
        patch("backend.services.jobs.runtime.connect_broker") as broker,
        patch("backend.services.jobs.runtime.process_message", side_effect=processing),
    ):
        broker.return_value.__enter__.return_value = (connection, channel)
        if persisted:
            consume_once(database, SETTINGS, "ingestion", stop)
            channel.basic_ack.assert_called_once_with(delivery_tag=7)
        else:
            with pytest.raises(StorageUnavailable):
                consume_once(database, SETTINGS, "ingestion", stop)
            channel.basic_ack.assert_not_called()
    channel.basic_qos.assert_called_once_with(prefetch_count=1)
    assert channel.basic_consume.call_args.kwargs["auto_ack"] is False
