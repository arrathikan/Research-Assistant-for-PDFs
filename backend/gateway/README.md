# FastAPI gateway

`backend.gateway.main:app` is the HTTP entry point. From the repository root,
with backend requirements installed and `.env` configured:

```bash
python -m uvicorn backend.gateway.main:app --host 127.0.0.1 --port 8000
```

Open `/docs` for the exact OpenAPI contract. `/health` and `/api/v1/health` are
process-liveness checks; they do not establish database, provider or search readiness.

## Responsibilities

- Validate multipart PDF bytes, size and structure before storage.
- Deduplicate SHA-256/GridFS uploads and ensure a durable MongoDB processing job.
- Read actual metadata/status, processing progress, published extraction/chunks,
  summaries and original bytes.
- Expose document-scoped chat/history, citation resolution, supported job retry
  and deletion. Slow parsing/summary work belongs to separately running workers.
- Use Pydantic validation, bounded request bodies, configured CORS and safe errors.
  CORS is not authentication or authorization; this is a local/demo application.

`POST /api/v1/documents` accepts one multipart field named `file`; `/upload` is a
compatibility alias. The client must let its HTTP library set multipart boundaries.
New writes return 201 and duplicates 200 with their actual state. Original PDFs
are complete in-memory responses, without byte-range streaming.

Run [the documented checks](../../docs/ci.md) from the root. Route details and
storage/worker/citation boundaries are summarized in [architecture](../../docs/architecture.md).
