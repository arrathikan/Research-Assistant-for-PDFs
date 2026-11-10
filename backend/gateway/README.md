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

