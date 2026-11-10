"""RAG Service entrypoint.

Implements Hybrid Retrieval (Voyage AI semantic search + BM25 keyword search + RRF)
and generates answers accompanied by precise PDF page citations.
"""

from backend.shared.config import get_settings
from backend.shared.logging import setup_logger

settings = get_settings()
logger = setup_logger("rag_service", settings.log_level)


def run_service():
    """Initializes the Hybrid RAG engine service."""
    logger.info("Initializing Hybrid RAG Service...")
    logger.info(f"Embedding model configured: {settings.voyage_model}")
    logger.info(f"LLM model configured: {settings.llm_model}")
    logger.info("RAG service skeleton ready. Hybrid retrieval & citations scheduled for Stage 6.")


if __name__ == "__main__":
    run_service()
