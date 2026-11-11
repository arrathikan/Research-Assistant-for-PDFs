"""Generate one stored PDF's summary explicitly; RabbitMQ dispatch comes later."""

import argparse

from backend.services.document_processor.chunk_cli import _document_id
from backend.services.document_processor.chunk_storage import ChunkingNotReady
from backend.services.summary_service.models import SummaryError
from backend.services.summary_service.storage import SummaryNotReady, summarize_stored_document
from backend.shared.config import get_settings
from backend.shared.database import StorageUnavailable, connect_database
from backend.shared.logging import setup_logger
from backend.shared.storage import DocumentNotFound


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a source-backed five-section research summary"
    )
    parser.add_argument("document_id", type=_document_id)
    args = parser.parse_args(argv)
    settings = get_settings()
    logger = setup_logger("summary_service", settings.log_level)
    try:
        with connect_database(settings) as database:
            summarize_stored_document(database, args.document_id, settings)
    except (
        SummaryError,
        SummaryNotReady,
        ChunkingNotReady,
        DocumentNotFound,
        StorageUnavailable,
    ) as error:
        logger.error(str(error))
        return 1
    logger.info(f"Summary published for {args.document_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
