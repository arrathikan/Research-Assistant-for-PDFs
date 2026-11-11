"""Explicit, resumable embedding job for one published chunk set."""

import argparse

from backend.services.document_processor.chunk_cli import _document_id
from backend.services.document_processor.chunk_storage import ChunkingNotReady
from backend.services.document_processor.embedding_storage import (
    EmbeddingConflict,
    EmbeddingNotReady,
    embed_stored_document,
)
from backend.shared.config import get_settings
from backend.shared.database import StorageUnavailable, connect_database
from backend.shared.embedding_models import EmbeddingError, EmbeddingInputError
from backend.shared.logging import setup_logger
from backend.shared.storage import DocumentNotFound


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Embed uncached chunks for one PDF using Voyage")
    parser.add_argument("document_id", type=_document_id)
    args = parser.parse_args(argv)
    settings = get_settings()
    logger = setup_logger("document_processor", settings.log_level)
    try:
        with connect_database(settings) as database:
            result = embed_stored_document(database, args.document_id, settings)
    except (
        EmbeddingError,
        EmbeddingInputError,
        EmbeddingNotReady,
        EmbeddingConflict,
        ChunkingNotReady,
        DocumentNotFound,
        StorageUnavailable,
    ) as exc:
        logger.error(str(exc))
        return 1
    logger.info(
        f"Embeddings complete for {args.document_id}: {result.chunk_count} chunks; awaiting summary"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
