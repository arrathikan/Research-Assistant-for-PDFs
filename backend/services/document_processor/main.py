"""Document Processor Worker entrypoint.

Subscribes to RabbitMQ document ingestion queue to parse uploaded research PDFs
using LlamaParse and generates Markdown-aware chunks with preserved page references.
"""

from backend.shared.config import get_settings
from backend.shared.logging import setup_logger

settings = get_settings()
logger = setup_logger("document_processor", settings.log_level)


def run_worker():
    """Initializes the background worker for PDF extraction and chunking."""
    logger.info("Initializing Document Processor worker...")
    logger.info(f"Target ingestion queue: {settings.ingestion_queue}")
    logger.info("Worker skeleton ready. Awaiting RabbitMQ events in Stage 3.")


if __name__ == "__main__":
    run_worker()
