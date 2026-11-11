"""One RabbitMQ I/O thread per consumer; provider work runs on a separate thread."""

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event

from backend.services.jobs.dispatch import dispatch_due, reconcile_requests
from backend.services.jobs.lifecycle import expire_jobs
from backend.services.jobs.processor import process_message
from backend.services.jobs.store import ensure_job_indexes
from backend.shared.broker import BrokerUnavailable, connect_broker, publish, queue_name
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable, connect_database
from backend.shared.job_models import DeadLetter, JobMessage, JobStage
from backend.shared.logging import setup_logger
from pika import BasicProperties
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPError
from pika.spec import Basic
from pydantic import ValidationError
from pymongo.database import Database


def consume_once(database: Database, settings: Settings, stage: JobStage, stop: Event) -> None:
    with (
        connect_broker(settings) as (connection, channel),
        ThreadPoolExecutor(max_workers=1) as executor,
    ):
        channel.basic_qos(prefetch_count=1)
        future: Future | None = None
        delivery_tag: int | None = None

        def received(
            ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes
        ) -> None:
            nonlocal future, delivery_tag
            try:
                if len(body) > 4096:
                    raise ValueError("Oversize envelope")
                message = JobMessage.model_validate_json(body)
                if message.stage != stage:
                    raise ValueError("Wrong queue")
            except (ValidationError, ValueError):
                publish(ch, DeadLetter(reason="INVALID_MESSAGE"), settings)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            record = database.processing_jobs.find_one(
                {"_id": message.job_id, "document_id": message.document_id}
            )
            if record is None:
                publish(ch, DeadLetter(reason="UNKNOWN_JOB", job=message), settings)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            delivery_tag = method.delivery_tag
            future = executor.submit(process_message, database, message, settings)

        channel.basic_consume(
            queue=queue_name(stage, settings), on_message_callback=received, auto_ack=False
        )
        while not stop.is_set() or future is not None:
            connection.process_data_events(time_limit=0.2)
            if future is not None and future.done():
                future.result()  # Failed persistence closes the connection without acknowledging.
                channel.basic_ack(delivery_tag=delivery_tag)
                future, delivery_tag = None, None
            if stop.is_set():
                # Cancel new deliveries while allowing current work to finish with heartbeats.
                if channel.consumer_tags:
                    channel.basic_cancel(channel.consumer_tags[0])


def worker_loop(settings: Settings, stage: JobStage, stop: Event) -> None:
    logger = setup_logger(f"jobs.{stage}", settings.log_level)
    while not stop.is_set():
        try:
            with connect_database(settings) as database:
                ensure_job_indexes(database)
                consume_once(database, settings, stage, stop)
        except (BrokerUnavailable, StorageUnavailable, AMQPError, OSError):
            logger.warning("Worker connection unavailable; retrying without discarding deliveries")
        except Exception:
            logger.error("Worker stopped unexpectedly; inspect job status before retrying")
        stop.wait(settings.job_poll_seconds)


def dispatcher_loop(settings: Settings, stop: Event) -> None:
    logger = setup_logger("jobs.dispatcher", settings.log_level)
    while not stop.is_set():
        try:
            with connect_database(settings) as database:
                ensure_job_indexes(database)
                with connect_broker(settings) as (connection, channel):
                    while not stop.is_set():
                        expire_jobs(database)
                        reconcile_requests(database, settings)
                        dispatch_due(database, channel, settings)
                        connection.process_data_events(time_limit=settings.job_poll_seconds)
        except (BrokerUnavailable, StorageUnavailable, AMQPError, OSError):
            logger.warning("Job dispatch unavailable; pending actions remain saved")
        except Exception:
            logger.error("Job dispatch failed; pending actions remain saved")
        stop.wait(settings.job_poll_seconds)
