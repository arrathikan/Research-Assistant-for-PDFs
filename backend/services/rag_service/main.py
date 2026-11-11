"""Run the same document-scoped chat pipeline used by the HTTP API."""

import argparse
import sys

from backend.services.document_processor.chunk_cli import _document_id
from backend.services.document_processor.chunk_storage import ChunkingNotReady
from backend.services.rag_service.models import (
    ChatRequest,
    RagConflict,
    RagNotReady,
    RagUnavailable,
)
from backend.services.rag_service.service import chat_with_trace
from backend.shared.config import get_settings
from backend.shared.database import StorageUnavailable, connect_database
from backend.shared.logging import setup_logger
from backend.shared.storage import DocumentNotFound
from pydantic import ValidationError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ask a question using the real document-scoped hybrid RAG pipeline"
    )
    parser.add_argument("document_id", type=_document_id)
    parser.add_argument("question")
    parser.add_argument("--conversation-id")
    args = parser.parse_args(argv)
    logger = setup_logger("rag_service")
    try:
        request = ChatRequest(message=args.question, conversation_id=args.conversation_id)
    except ValidationError:
        logger.error("Invalid question or conversation identifier")
        return 1
    try:
        settings = get_settings()
        with connect_database(settings) as database:
            output = chat_with_trace(database, args.document_id, request, settings)
    except (
        RagConflict,
        RagNotReady,
        RagUnavailable,
        ChunkingNotReady,
        StorageUnavailable,
        DocumentNotFound,
    ) as error:
        logger.error(str(error))
        return 1
    sys.stdout.write(output.response.model_dump_json(indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
