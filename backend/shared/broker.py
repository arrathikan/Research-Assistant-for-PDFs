"""Durable RabbitMQ queues and confirmed publications using the approved Pika client."""

from collections.abc import Iterator
from contextlib import contextmanager

import pika
from backend.shared.config import Settings
from backend.shared.job_models import DeadLetter, JobMessage, JobStage
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
from pika.exceptions import AMQPError


class BrokerUnavailable(RuntimeError):
    """Safe broker failure without connection strings or message content."""


def queue_name(stage: JobStage, settings: Settings) -> str:
    return settings.ingestion_queue if stage == "ingestion" else settings.summary_queue


def declare_queues(channel: BlockingChannel, settings: Settings) -> None:
    for name in (settings.ingestion_queue, settings.summary_queue):
        channel.queue_declare(
            queue=name,
            durable=True,
            arguments={"x-consumer-timeout": settings.worker_ack_timeout_ms},
        )
    channel.queue_declare(queue=settings.dlq_queue, durable=True)
    channel.confirm_delivery()


@contextmanager
def connect_broker(settings: Settings) -> Iterator[tuple[BlockingConnection, BlockingChannel]]:
    connection = None
    try:
        parameters = pika.URLParameters(settings.rabbitmq_url)
        parameters.heartbeat = settings.rabbitmq_heartbeat_seconds
        parameters.socket_timeout = settings.rabbitmq_connection_timeout_seconds
        parameters.stack_timeout = settings.rabbitmq_connection_timeout_seconds + 5
        parameters.blocked_connection_timeout = settings.rabbitmq_connection_timeout_seconds
        parameters.connection_attempts = 1
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        declare_queues(channel, settings)
        yield connection, channel
    except (AMQPError, OSError, ValueError):
        raise BrokerUnavailable("Message broker unavailable") from None
    finally:
        if connection is not None and connection.is_open:
            try:
                connection.close()
            except (AMQPError, OSError):
                pass


def publish(channel: BlockingChannel, message: JobMessage | DeadLetter, settings: Settings) -> None:
    destination = (
        settings.dlq_queue
        if isinstance(message, DeadLetter)
        else queue_name(message.stage, settings)
    )
    identifier = (
        message.job.message_id()
        if isinstance(message, DeadLetter) and message.job
        else message.message_id()
        if isinstance(message, JobMessage)
        else None
    )
    try:
        channel.basic_publish(
            exchange="",
            routing_key=destination,
            body=message.model_dump_json().encode(),
            properties=pika.BasicProperties(
                content_type="application/json", delivery_mode=2, message_id=identifier
            ),
            mandatory=True,
        )
    except (AMQPError, OSError):
        raise BrokerUnavailable("Job publication was not confirmed") from None
