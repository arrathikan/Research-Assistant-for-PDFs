# ResearchAI — Research Assistant for PDFs

ResearchAI helps students and researchers understand academic papers through
structured summaries, document-grounded chat, and citations linked to the
original PDF. A React workspace connects to a FastAPI gateway and background
workers that handle parsing, embeddings, and summary generation.

[Local development](#local-development) · [Docker](#run-with-docker) ·
[Troubleshooting](#troubleshooting) · [Documentation](#documentation)

## Features

- **PDF upload:** structure validation, a default 25 MiB limit, and SHA-256
  deduplication to recognize papers already stored.
- **Five-part summaries:** Title, Authors and Abstract; Problem Statement;
  Methodology; Key Results; and Conclusion.
- **Research chat:** paper-specific questions, metadata questions, and follow-ups,
  with general background clearly distinguished from paper evidence.
- **Hybrid retrieval:** MongoDB Atlas semantic search and BM25 keyword search
  combined with reciprocal rank fusion (RRF).
- **Source navigation:** clickable page citations open an optional PDF viewer.
  Accurate passage highlighting is used when supported; otherwise, the viewer
  opens the cited page.
- **Paper library:** filename search, status filters, sorting, original PDF
  downloads, and document deletion. Document references are restored within the
  same browser session.
- **Background processing:** real processing states, bounded retries, and saved
  stage outputs. Uploading a file does not imply processing has finished.

## Technology stack

| Layer | Technologies |
| --- | --- |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| PDF viewer | React-PDF / PDF.js |
| API | Python, FastAPI, Pydantic, PyMongo |
| Storage and search | MongoDB Atlas, GridFS, Atlas Vector Search, MongoDB Search |
| Background jobs | RabbitMQ with separate dispatcher, ingestion, and summary workers |
| AI pipeline | LlamaParse, LangChain, Voyage AI embeddings, LangGraph, OpenRouter |
| Testing | pytest, Ruff, Vitest, Playwright; optional offline Ragas |
| Operations | Docker Compose, Nginx, GitHub Actions |

## Architecture

```mermaid
flowchart TD
    UI[React workspace] --> API[FastAPI gateway]
    API --> STORE[MongoDB metadata and GridFS PDFs]
    API --> OUTBOX[MongoDB job outbox]
    OUTBOX --> DISPATCH[Job dispatcher]
    DISPATCH --> MQ[RabbitMQ]
    MQ --> WORKERS[Ingestion and summary workers]
    WORKERS --> PARSE[LlamaParse pages and Markdown]
    PARSE --> CHUNKS[LangChain Markdown-aware chunks]
    CHUNKS --> EMB[Voyage document embeddings]
    EMB --> SEARCH[Atlas vector and keyword indexes]
    CHUNKS --> SUMMARY[LangGraph summary with OpenRouter]
    SUMMARY --> STORE
    API --> CHAT[Document-scoped chat with OpenRouter]
    CHAT <--> SEARCH
    CHAT --> SOURCES[Server-validated citations]
    SOURCES --> UI
    UI --> PDF[Optional original PDF viewer]
```

The gateway and workers share a Python codebase but run as separate processes.
Workers perform slow document processing outside upload requests. Ragas evaluation
is separate from normal summary and chat requests.

The default chunking configuration uses Markdown-aware splitting with a maximum
of 1,200 characters and a target overlap of 150 characters. Retrieval is scoped
to the selected document and source generation. See the
[architecture](docs/architecture.md), [chunking](docs/markdown-chunking.md), and
[hybrid retrieval](docs/hybrid-rag.md) guides for implementation details.

## Prerequisites

| Requirement | Local development | Full Docker setup |
| --- | --- | --- |
| Git | Required | Required |
| Python | 3.12 recommended; project declares 3.11+ | Included in the backend image |
| Node.js | 22 | Included in the frontend build image |
| Docker with Compose 2.24+ | Runs RabbitMQ | Runs the frontend, API, workers, and RabbitMQ |
| MongoDB Atlas | Required for live hybrid search | Required for live hybrid search |
| Provider accounts | LlamaParse, Voyage AI, and OpenRouter with available quota | Same |

Docker Desktop must be running when using Docker commands. Python 3.12 is used
in CI and the backend image. Ordinary local MongoDB supports storage tests but
does not provide this application's Atlas Vector Search and BM25 retrieval.

Choose **one application mode** at a time:

| Mode | Application URL | API URL |
| --- | --- | --- |
| Local: Vite, Python API/workers, Docker RabbitMQ | `http://localhost:5173` | `http://localhost:8000` |
| Docker: all application services in containers | `http://localhost:3000` | `http://localhost:8000` |

Both modes use the same default API port and job queues. Stop the current mode
before switching; changing a port alone does not isolate the background workers.

## Project and configuration

The terminal commands below use Bash or Zsh on macOS/Linux. Open your existing
project folder in VS Code. For a new checkout:

```bash
git clone https://github.com/arrathikan/Research-Assistant-for-PDFs.git
cd Research-Assistant-for-PDFs
```

The command blocks below assume the terminal is somewhere inside this Git
checkout. Their first `cd` command returns to the repository root, including when
the terminal was previously inside `frontend`.

Create the root `.env` only if it does not already exist:

```bash
cd "$(git rev-parse --show-toplevel)"
if [ ! -f .env ]; then
    cp .env.example .env
fi
```

Edit `.env` locally, preserving existing credentials. The main settings are:

| Setting | Purpose |
| --- | --- |
| `MONGODB_URI` | Your Atlas connection string; replace the storage-only local template URI |
| `MONGODB_DB_NAME` | Application database; default `research_assistant` |
| `RABBITMQ_URL` | Local Python broker URL; default `amqp://guest:guest@localhost:5672/` |
| `LLAMA_CLOUD_API_KEY` | LlamaParse PDF extraction |
| `VOYAGE_API_KEY` | Direct Voyage embedding requests |
| `VOYAGE_EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS` | Embedding profile; must match the Atlas vector index |
| `OPENROUTER_API_KEY` | OpenRouter authentication for summary and chat completions |
| `PRIMARY_REASONING_MODEL` | An available OpenRouter model supporting the required structured output |
| `CORS_ORIGINS` | Allowed browser origins; defaults include localhost ports 5173 and 3000 |

OpenRouter credentials belong in `OPENROUTER_API_KEY`. `OPENAI_API_KEY` is not used
by the application's completion client, and `OPENROUTER_BASE_URL` does not change
its fixed OpenRouter endpoint. See [provider configuration](docs/provider-configuration.md)
for model roles, timeouts, optional settings, and embedding compatibility.

In the **Atlas project matching your connection string**, allow your current
public IP address under Network Access and configure database/search-index
permissions. Update the allowlist when your public IP changes. Follow the
[Atlas setup guide](docs/atlas-setup.md) for database users and connection details.

Keep `.env`, credentials, private papers, and private chat traces out of version
control. Frontend `VITE_` variables are public. Native Vite reads
`frontend/.env.local` or exported variables, not the root `.env`; its default API
URL is already `http://localhost:8000/api/v1`. Restart the affected processes after
changing their environment settings.

## Local development

### First-time installation

Run once, or repeat dependency installation after requirements change:

```bash
cd "$(git rev-parse --show-toplevel)"
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd frontend
npm ci
```

Use the project's `.venv` in every backend terminal. An existing Anaconda
environment may not contain the project's dependencies.

### Initialize Atlas

With `.env` configured, initialize the application's collection indexes:

```bash
cd "$(git rev-parse --show-toplevel)"
source .venv/bin/activate
python -m backend.shared.database
```

For a new database, create the empty `chunk_embeddings` collection in Atlas
Collections first, then request the search indexes:

```bash
python -m backend.services.rag_service.indexes --create
```

Wait for `chunk_embeddings_v1` and `chunk_keywords_v1` to become queryable in
Atlas, or use the names configured in `.env`. The creation command does not wait
for readiness; running it without `--create` only prints definitions.
[Atlas initialization details](docs/atlas-setup.md#6-initialize-storage-and-search)
include an alternative to creating the collection in the UI.

### Daily startup: three VS Code terminals

Keep each process in its own terminal. Start each service once.

**Terminal 1 — RabbitMQ and API**

```bash
cd "$(git rev-parse --show-toplevel)"
source .venv/bin/activate
docker compose up -d rabbitmq
python -m uvicorn backend.gateway.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Background workers**

```bash
cd "$(git rev-parse --show-toplevel)"
source .venv/bin/activate
python -m backend.services.jobs.main run
```

`Background processing started; shutdown waits for in-flight work` is a normal
startup message. Keep this terminal open for PDF processing.

**Terminal 3 — Frontend**

```bash
cd "$(git rev-parse --show-toplevel)"
cd frontend
npm run dev -- --host localhost --strictPort
```

`--strictPort` reports a port conflict instead of silently moving to another
frontend port. Open [ResearchAI](http://localhost:5173) or the
[interactive API documentation](http://localhost:8000/docs).

### Stop local development

Press **Control + C** in each API, worker, and frontend terminal. Workers wait for
in-flight work before exiting; wait for the terminal prompt to return.

After workers stop, stop RabbitMQ if it is no longer needed:

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose stop rabbitmq
```

This keeps the broker's persistent data. Stop these local processes before
starting the full Docker application.

## Run with Docker

With the root `.env` configured and local application processes stopped:

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose up -d --build --wait
docker compose ps
```

This starts the built React application through Nginx, the API, the background
workers, and RabbitMQ. Open [ResearchAI](http://localhost:3000). Separate Uvicorn,
worker, and `npm run dev` terminals are not needed in this mode.

For a new Atlas database, initialize storage using the running container:

```bash
docker compose exec -T gateway python -m backend.shared.database
```

Create the empty `chunk_embeddings` collection in Atlas if it is missing, then:

```bash
docker compose exec -T gateway python -m backend.services.rag_service.indexes --create
```

Wait for the search indexes to become queryable before using chat. Docker does
not replace Atlas or automatically configure its network access and search indexes.

To inspect services and recent logs:

```bash
docker compose ps
docker compose logs --tail=50 gateway workers
docker compose config -q
```

Use `config -q` for configuration validation. Plain `docker compose config`
expands credentials into its output.

To stop the container application while retaining persistent data:

```bash
docker compose stop
```

See [Docker operations](docs/deployment.md) for port overrides, the optional local
MongoDB storage profile, shutdown behavior, and isolated container smoke tests.

## Using ResearchAI

1. Upload one academic PDF and wait for its actual processing status.
2. Once ready, open the five-part Structured Summary or Chat with Paper.
3. Ask about the authors, methodology, findings, limitations, or a specific topic.
4. Click a source citation to open the original PDF at the cited page. The PDF
   viewer stays closed until requested and can be closed without clearing chat.
5. Use the paper menu to download the original or confirm document deletion.

An uploaded file can still be queued or processing. A successful API health check
only confirms HTTP liveness; it does not prove Atlas connectivity, search-index
readiness, provider access, or successful processing of a particular PDF.

## Troubleshooting

| Message or symptom | Meaning and next step |
| --- | --- |
| `No module named 'backend'` | Run from the repository root, not `frontend`. Use the first `cd` command in the local startup blocks. |
| `No module named 'llama_cloud'` or another dependency | Activate `.venv` and run `python -m pip install -r backend/requirements.txt` from the root. |
| `[Errno 48] Address already in use` | An API is already using port 8000. Use the existing instance or stop it in its terminal before restarting. Check whether full Docker mode is still running. |
| Frontend port already in use | Another frontend is running. Reuse it or stop it before starting another Vite process. |
| `Background processing started` | Successful worker startup; keep the terminal open. |
| `LangChainPendingDeprecationWarning` | A library notice about a future change; this warning alone is not a startup failure. Check the following log lines for actual errors. |
| Upload fails or reports a connection problem | Confirm the API is running, the frontend uses its correct URL, and Atlas storage is accessible. Inspect the API terminal or gateway logs. |
| Paper stays queued or workers repeatedly retry connections | Confirm workers and RabbitMQ are running and Atlas is reachable. A running frontend alone cannot process PDFs. |
| MongoDB timeout or TLS connection error | Check the configured cluster, current-IP allowlist, database credentials, and network/TLS connectivity. A TLS error does not by itself prove an allowlist problem. |
| OpenRouter HTTP `402` or `429` | Check the account's credits/key spending limit or provider quota/rate limit, respectively. Confirm the configured model is available to that key. |

For a safe API liveness check:

```bash
curl --fail http://localhost:8000/health
```

Processing failures and interrupted jobs have different retry rules. Follow
[background job recovery](docs/background-jobs.md) rather than manually editing
job records or repeatedly starting additional workers.

## Testing and evaluation

### Backend

The full backend suite also tests offline evaluation adapters. Use a separate
test/evaluation environment so optional Ragas dependencies do not change the
serving environment:

```bash
cd "$(git rev-parse --show-toplevel)"
python3 -m venv .venv-evaluation
source .venv-evaluation/bin/activate
python -m pip install -r backend/requirements.txt -r evaluation/requirements.txt
python -m pytest backend/tests -m 'not live_parser and not live_rag and not live_summary' -q
ruff check backend
ruff check --config backend/pyproject.toml scripts/compose_smoke.py
```

MongoDB/RabbitMQ integration tests require isolated services and explicit opt-in
settings; otherwise, they skip. Paid provider tests are excluded above.

### Frontend

```bash
cd "$(git rev-parse --show-toplevel)"
cd frontend
npm test
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

The default browser suite uses deterministic fixtures and its own test server.
There is no separate frontend lint script. [CI](.github/workflows/ci.yml) runs
Python lint/tests, frontend tests and build, browser checks, and an isolated
Docker smoke test. See the [CI guide](docs/ci.md) for details and integration settings.

### Offline Ragas evaluation

Ragas is optional and separate from live chat. Its workflow records retrieved
contexts, answers, citations, model settings, and measured metrics for review.
Full model-based evaluation consumes provider requests and is run explicitly,
outside normal CI. Follow the [evaluation guide](evaluation/README.md) and read
the [published results](evaluation/reports/README.md) with their coverage and
failure notes. Assistant source reviews are identified as such and do not
constitute independent human approval.

## Project structure

```text
backend/gateway/                  FastAPI routes and HTTP contracts
backend/services/                 document processing, jobs, summaries, and RAG
backend/shared/                   configuration, storage, and provider clients
backend/tests/                    unit and opt-in integration/provider tests
frontend/src/                     React application and unit tests
frontend/e2e/                     browser tests
evaluation/                      offline Ragas tooling, datasets, and reports
docs/                            architecture, setup, operations, and QA evidence
scripts/compose_smoke.py          isolated container smoke check
.github/workflows/ci.yml          continuous integration
```

## Documentation

| Topic | Guide |
| --- | --- |
| Architecture and implementation status | [Architecture](docs/architecture.md), [roadmap](docs/development-roadmap.md) |
| Atlas and providers | [Atlas setup](docs/atlas-setup.md), [provider configuration](docs/provider-configuration.md) |
| Processing and retrieval | [Background jobs](docs/background-jobs.md), [summaries](docs/structured-summary.md), [hybrid RAG](docs/hybrid-rag.md) |
| Citations and PDF navigation | [PDF citations](docs/pdf-citations.md) |
| Operations and QA | [Docker](docs/deployment.md), [CI](docs/ci.md), [browser QA](docs/browser-qa.md) |
| Demo and verification | [Demo guide](docs/demo-guide.md), [submission review](docs/submission-review.md), [actual UI screenshots](docs/screenshots.md) |

The [documentation index](docs/README.md) distinguishes current technical guides
from dated design and verification records. Screenshots and QA reports state
their scope; they are not a guarantee that every paper or provider call succeeds.

## Current limitations

- This is a local/demo application without authentication, authorization, or a
  public TLS deployment.
- Provider quota, model/schema support, latency, Atlas network access, and index
  readiness affect availability.
- Full-paper summaries can fail strict quote validation. Citation provenance
  checks do not guarantee scientific correctness; important findings need review.
- Passage highlighting depends on reliable text or geometry and can fall back
  to page navigation.
- The library is session-based, not an account-based, cross-device library.
- Existing dependency advisories require remediation; see the submission review.
- Evaluation coverage is limited and includes incomplete runs. No universal
  accuracy score or general hybrid-over-semantic advantage is claimed.

## Maintainer

Maintained by [arrathikan](https://github.com/arrathikan). Existing contribution
history and public-paper attribution are preserved in the repository and its
evaluation documentation.
