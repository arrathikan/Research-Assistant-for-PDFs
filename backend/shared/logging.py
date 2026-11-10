"""JSON logging without request bodies, query strings, or provider secrets."""

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": record.name,
            "message": record.getMessage(),
        }
        for field in ("request_id", "method", "status_code", "duration_ms"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        return json.dumps(payload)


def setup_logger(service_name: str, log_level: str = "INFO") -> logging.Logger:
    """Configure one JSON handler per service."""
    logger = logging.getLogger(service_name)
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.propagate = False
    return logger
