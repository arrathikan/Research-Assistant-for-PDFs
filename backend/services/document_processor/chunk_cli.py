"""Chunk one published parse without calling a parser, embedding model or LLM."""

import argparse

from backend.services.document_processor.chunk_models import ChunkingConfig, ChunkingError
from backend.services.document_processor.chunk_storage import (
    ChunkingConflict,
    ChunkingNotReady,
    chunk_stored_document,
)
from backend.services.document_processor.extraction import ParsingNotReady
from backend.shared.config import get_settings
from backend.shared.database import StorageUnavailable, connect_database
from backend.shared.logging import setup_logger
from backend.shared.storage import DocumentNotFound
from bson import ObjectId
from pydantic import ValidationError


def _document_id(value: str) -> str:
    if not ObjectId.is_valid(value):
        raise argparse.ArgumentTypeError("document_id must be a MongoDB ObjectId")
    return str(ObjectId(value))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create source-attributed Markdown chunks for one parsed PDF"
    )
    parser.add_argument("document_id", type=_document_id)
    parser.add_argument("--chunk-size", type=int)
    parser.add_argument("--chunk-overlap", type=int)
    args = parser.parse_args(argv)
    settings = get_settings()
    logger = setup_logger("document_processor", settings.log_level)
    try:
        config = ChunkingConfig(
            chunk_size=args.chunk_size if args.chunk_size is not None else settings.chunk_size,
            chunk_overlap=args.chunk_overlap
            if args.chunk_overlap is not None
            else settings.chunk_overlap,
        )
    except ValidationError:
        logger.error("Invalid chunk configuration: require size > 0 and 0 <= overlap < size")
        return 1
    settings = settings.model_copy(update=config.model_dump())
    try:
        with connect_database(settings) as database:
            chunks = chunk_stored_document(database, args.document_id, settings)
    except (
        ChunkingError,
        ChunkingNotReady,
        ChunkingConflict,
        ParsingNotReady,
        DocumentNotFound,
        StorageUnavailable,
    ) as exc:
        logger.error(str(exc))
        return 1
    logger.info(
        f"Chunking complete for {args.document_id}: {len(chunks)} chunks; awaiting embeddings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
