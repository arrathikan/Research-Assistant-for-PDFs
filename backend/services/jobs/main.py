"""Run workers independently of the gateway, or explicitly recover reviewed work."""

import argparse
import signal
from threading import Event, Thread

from backend.services.document_processor.chunk_cli import _document_id
from backend.services.jobs.lifecycle import recover_interrupted
from backend.services.jobs.runtime import dispatcher_loop, worker_loop
from backend.services.jobs.store import JobConflict
from backend.shared.config import get_settings
from backend.shared.database import StorageUnavailable, connect_database
from backend.shared.logging import setup_logger
from backend.shared.storage import DocumentNotFound


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ResearchAI RabbitMQ background processing")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("run", help="Run dispatcher, ingestion worker and summary worker")
    commands.add_parser("dispatch", help="Run the durable outbox dispatcher only")
    work = commands.add_parser("work", help="Consume one processing queue")
    work.add_argument("stage", choices=("ingestion", "summary"))
    recovery = commands.add_parser("recover", help="Recover an expired job after operator review")
    recovery.add_argument("document_id", type=_document_id)
    recovery.add_argument("--confirm-workers-stopped", action="store_true", required=True)
    args = parser.parse_args(argv)
    settings = get_settings()
    logger = setup_logger("jobs", settings.log_level)
    if args.command == "recover":
        try:
            with connect_database(settings) as database:
                recover_interrupted(database, args.document_id, settings)
        except (JobConflict, StorageUnavailable, DocumentNotFound) as failure:
            logger.error(str(failure))
            return 1
        logger.info("Reviewed interrupted job rescheduled; completed outputs retained")
        return 0
    stop = Event()
    previous = {}
    for name in (signal.SIGINT, signal.SIGTERM):
        previous[name] = signal.signal(name, lambda *_: stop.set())
    targets = (
        [
            (dispatcher_loop, (settings, stop)),
            (worker_loop, (settings, "ingestion", stop)),
            (worker_loop, (settings, "summary", stop)),
        ]
        if args.command == "run"
        else [(dispatcher_loop, (settings, stop))]
        if args.command == "dispatch"
        else [(worker_loop, (settings, args.stage, stop))]
    )
    threads = [
        Thread(target=target, args=arguments, name=f"jobs-{index}")
        for index, (target, arguments) in enumerate(targets)
    ]
    try:
        for thread in threads:
            thread.start()
        logger.info("Background processing started; shutdown waits for in-flight work")
        while not stop.wait(1):
            if not all(thread.is_alive() for thread in threads):
                logger.error("Background worker exited; stopping remaining processes")
                stop.set()
        for thread in threads:
            thread.join()
    finally:
        for name, handler in previous.items():
            signal.signal(name, handler)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
