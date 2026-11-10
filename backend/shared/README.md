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
logger.info("Storage configuration loaded")
```


## MongoDB connection and initialization (Prompt 4.1)

Use `connect_database(settings)` as a context manager and explicitly call
`ensure_indexes(database)` before accepting document writes. The connection is
closed on success or failure. Driver messages and connection URIs are never
logged by these helpers. Synchronous PyMongo operations must run in workers or
synchronous FastAPI handlers.

```bash
python -m backend.shared.database
```

This command creates indexes for `documents`, `chunks`, `source_elements`,
`summaries`, `chat_messages`, and `processing_jobs`. It requires index creation
permissions. A unique SHA-256 index protects concurrent document writes; existing
duplicates cause initialization to fail without modifying data. MongoDB's `_id`
is the document identifier; related collections use its string as `document_id`.

`MONGODB_URI` supports local MongoDB and Atlas `mongodb+srv://` connections.
Use Atlas TLS defaults, a least-privilege database user and an IP access list.
Do not disable TLS verification or commit credentials. Configure
`MONGODB_DB_NAME` and positive `MONGODB_TIMEOUT_MS` (default 5000). Health routes
remain process liveness checks and do not connect to MongoDB.
