"""Summary Service entrypoint.

Executes a deterministic LangGraph state machine to extract a 5-part academic summary:
1. Title, Authors, and Abstract
2. Problem Statement
3. Methodology
4. Key Results
5. Conclusion
"""

from backend.shared.config import get_settings
from backend.shared.logging import setup_logger

settings = get_settings()
logger = setup_logger("summary_service", settings.log_level)


def run_service():
    """Initializes the LangGraph summarization service."""
    logger.info("Initializing Summary Service...")
    logger.info(f"Target summary queue: {settings.summary_queue}")
    logger.info("Summary service skeleton ready. LangGraph workflow scheduled for Stage 5.")


if __name__ == "__main__":
    run_service()
