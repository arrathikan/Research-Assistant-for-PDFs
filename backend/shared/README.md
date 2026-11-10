# Shared Backend Library (`backend/shared/`)

This directory contains cross-cutting utilities, Pydantic data schemas, shared configuration, and logging infrastructure utilized by the API gateway and individual microservices.

---

## Structure

- **`config.py`**: Centralized configuration management using Pydantic `BaseSettings`. Loads environment variables from `.env` with type validation and sensible defaults.
- **`models.py`**: Shared domain models and validation contracts:
  - `DocumentStatus`: Document processing lifecycle enum.
  - `DocumentMetadata`: PDF metadata and GridFS file reference.
  - `ChunkMetadata`: Chunk schema with page and section metadata.
  - `StructuredSummary`: 5-part academic summary schema.
  - `CitationReference`: Page number and quote snippet model.
  - `ChatQueryRequest` / `ChatQueryResponse`: Conversational RAG contracts.
- **`logging.py`**: Standardized stream logger ensuring uniform timestamping and log formatting across all services.

---

## Usage Example

```python
from backend.shared.config import get_settings
from backend.shared.logging import setup_logger
from backend.shared.models import DocumentMetadata, DocumentStatus

settings = get_settings()
logger = setup_logger("my_service", settings.log_level)
logger.info(f"Connected to {settings.mongodb_uri}")
```

