"""Parse one stored document explicitly; automatic jobs use services.jobs.main."""

import argparse

from backend.services.document_processor.extraction import ParsingConflict, parse_pdf
from backend.services.document_processor.parsed_models import ParsingError
from backend.shared.config import get_settings
from backend.shared.database import StorageUnavailable, connect_database
from backend.shared.logging import setup_logger
from backend.shared.storage import DocumentNotFound
from bson import ObjectId


def _document_id(value: str) -> str:
    if not ObjectId.is_valid(value):
        raise argparse.ArgumentTypeError("document_id must be a MongoDB ObjectId")
    return str(ObjectId(value))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract one uploaded PDF with LlamaParse")
    parser.add_argument("document_id", type=_document_id)
    args = parser.parse_args(argv)
    settings = get_settings()
    logger = setup_logger("document_processor", settings.log_level)
    if not settings.llama_cloud_api_key.strip() or settings.llama_cloud_api_key.startswith("your_"):
        logger.error("Configure LLAMA_CLOUD_API_KEY before parsing")
        return 1
    try:
        with connect_database(settings) as database:
            parsed = parse_pdf(database, args.document_id, settings)
    except (ParsingError, ParsingConflict, StorageUnavailable, DocumentNotFound) as exc:
        logger.error(str(exc))
        return 1
    logger.info(
        f"Extraction complete for {args.document_id}: {len(parsed.pages)} pages; awaiting the next processing stage"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
