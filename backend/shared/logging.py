"""Structured logging configuration for ResearchAI microservices."""

import logging
import sys


def setup_logger(service_name: str, log_level: str = "INFO") -> logging.Logger:
    """Configures and returns a standardized logger for a given microservice."""
    logger = logging.getLogger(service_name)
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False
    return logger
