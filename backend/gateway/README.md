# API Gateway (`backend/gateway/`)

The API Gateway is the primary HTTP interface connecting frontend clients with backend microservices and databases.

---

## Responsibilities

1. **Routing & Orchestration:** Exposes REST endpoints under `/api/v1/` for document management, status querying, summaries, and chat.
2. **Request Validation:** Validates incoming payloads using shared Pydantic v2 schemas (`backend.shared.models`).
3. **CORS & Security:** Enforces origin checks and security headers.
4. **Health Checks:** Exposes `/health` and `/api/v1/health` for orchestrators and monitoring tools.

---

## Running Locally

```bash
uvicorn backend.gateway.main:app --host 0.0.0.0 --port 8000 --reload
```


## Implemented gateway contract (Prompt 3)

- `GET /health`: process liveness, environment and application version.
- `GET /api/v1/health`: versioned, schema-validated liveness response.
- `/docs` and `/openapi.json`: generated API contract.
- Errors use a string `detail` compatible with the React API client. Invalid
  requests return 422; unexpected errors return a generic 500. Bodies and provider
  exception messages are excluded from error responses and request logs.
- Requests receive an `X-Request-ID` and JSON duration/status log entries.
- CORS allows configured origins and GET/POST/OPTIONS; the request ID is exposed.

Health is **liveness only**: it does not establish MongoDB, RabbitMQ, or AI-provider
readiness. No database or PDF routes are implemented by this increment.

Configure `CORS_ORIGINS` as a JSON array, for example
`["http://localhost:5173"]`. Existing environment settings remain supported.

From the repository root, in an environment with the gateway dependencies:

```bash
python -m pytest backend/tests -q
ruff check --no-cache backend/gateway backend/shared/logging.py backend/tests/test_gateway_contracts.py
ruff format --check backend/gateway backend/shared/logging.py backend/tests/test_gateway_contracts.py
```

Linting currently covers the Prompt 3 files; older scaffolding is not reformatted.

## Document upload API (Prompt 5)

- `POST /api/v1/documents`: one multipart `file`; 201 for a new document,
  200 for an identical existing document. `/api/v1/documents/upload` is a
  compatibility alias for earlier frontend clients.
- Response: `{document: {id, sha256, filename, file_size_bytes, page_count,
  status, ...}, is_duplicate, message}`. Public identifiers use `id`, not `_id`.
- `GET /api/v1/documents/{id}`: persisted metadata.
- `GET /api/v1/documents/{id}/status`: document ID, actual status and error.
- `GET /api/v1/documents/{id}/pdf`: original bytes with inline PDF disposition.

The upload parser accepts exactly one file, no additional fields, and caps
received body bytes at the configured file limit plus 64 KiB for multipart
headers. The actual file has its own strict size check. Body limits count bytes
even without Content-Length. Multipart spool files close on success or rejection
and use the operating system's temporary directory, outside the repository.
Validation and synchronous PyMongo work run in the thread pool. A unique SHA-256
index is ensured before every accepted write.

Invalid/corrupt/empty/encrypted PDFs return 400, oversize files/requests 413,
unsupported MIME/encoding 415, missing/wrong file field 422 (multipart structure
errors may be 400), missing documents/files 404, invalid IDs 422, and storage
unavailability 503. Internal storage details are not exposed.

New documents remain `PENDING`. No parsing, summary generation, chat, RabbitMQ
publication or simulated success is performed. A duplicate returns its actual
stored status, including pending or failed records. Status does not advance
until later processing stages are installed. Original downloads are complete
responses in memory; byte-range streaming is not implemented yet.

```bash
curl -F 'file=@/absolute/path/paper.pdf' http://localhost:8000/api/v1/documents
curl http://localhost:8000/api/v1/documents/DOCUMENT_ID/status
curl http://localhost:8000/api/v1/documents/DOCUMENT_ID/pdf --output /tmp/original.pdf
```

## Published extraction (Prompt 6)

`GET /api/v1/documents/{id}/parsed` returns the completed parse's per-page Markdown
and source elements. It returns 409 until a complete run is published, 404 for an
unknown document and 422 for malformed identifiers. This endpoint never starts a
paid cloud call. Run the document processor CLI separately after configuration.
Metadata now includes parsing_status and parsed_at; completed extraction alone
does not mark a document READY for summaries/chat.

## Published chunks (Prompt 7)

`GET /api/v1/documents/{id}/chunks` returns the complete active chunk set with
page spans, heading metadata and source references. It never starts chunking or
embedding. Unfinished/current-parse mismatches return 409; unknown IDs 404,
malformed IDs 422 and storage failures 503. CLI processing is separate.
