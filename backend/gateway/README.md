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
