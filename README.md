# ResearchAI — AI-Powered Research Paper Assistant

**Understand research papers faster. Ask questions with confidence. Verify answers against their sources.**

ResearchAI is a full-stack research assistant that converts academic PDFs into structured summaries and supports document-grounded conversations with navigable citations. It combines **Hybrid Retrieval-Augmented Generation (RAG)**, stateful AI workflows, and asynchronous document processing in a responsive research workspace.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-TypeScript-149ECA?logo=react&logoColor=white)](https://react.dev/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

[Architecture](docs/architecture.md) · [Evaluation](evaluation/README.md) · [Deployment](docs/deployment.md)

[Local development](#local-development) · [Docker](#run-with-docker) · [Troubleshooting](#troubleshooting) · [Documentation](#documentation)

## Why ResearchAI?

Research papers contain dense methodologies, experiments, and specialized terminology. Generic AI chat interfaces can help explain them, but answers may lack traceable support from the original document. ResearchAI focuses on **source-grounded understanding**: users can upload a paper, read a consistent summary, ask questions, and open cited evidence directly in the PDF.

## Key Features

- **Five-part research summaries:** Title/authors/abstract, problem and motivation, methodology, results, and conclusions/future work.
- **Hybrid RAG:** Voyage AI embeddings and MongoDB Atlas Vector Search combined with BM25 keyword retrieval through Reciprocal Rank Fusion (RRF).
- **Evidence-aware answers:** Document-scoped retrieval, source-reference validation, and an abstention path when evidence is insufficient.
- **Interactive citations:** Open the original PDF at the referenced page, with text/region highlighting when available and page-only fallback otherwise.
- **Background processing:** RabbitMQ workers handle PDF parsing, chunking, embeddings, and summaries with retry and recovery mechanisms.
- **Research workspace:** PDF upload, filename search, status tracking, filtering, sorting, deletion, and saved conversations.
- **Offline RAG evaluation:** Ragas metrics and manual source reviews for answer and retrieval quality.

## System Architecture

```mermaid
flowchart TD
    UI["React + TypeScript"] --> API["FastAPI Gateway"]
    API --> DB[("MongoDB Atlas + GridFS")]
    API --> JOB["Durable Processing Jobs"]
    JOB --> MQ["RabbitMQ"]
    MQ --> WORKER["Background Worker"]
    WORKER --> PARSE["LlamaParse"]
    PARSE --> CHUNK["Markdown-Aware Chunking"]
    CHUNK --> EMBED["Voyage AI Embeddings"]
    EMBED --> DB
    WORKER --> SUM["LangGraph Summary"]
    SUM --> DB
    API --> RAG["Document-Scoped Hybrid RAG"]
    RAG --> VECTOR["Atlas Vector Search"]
    RAG --> KEYWORD["BM25 Keyword Search"]
    VECTOR --> RRF["Reciprocal Rank Fusion"]
    KEYWORD --> RRF
    RRF --> LLM["LLM via OpenRouter"]
    LLM --> CIT["Citation Validation"]
    CIT --> API
```

### Document Processing

1. **Validate and store:** Check uploaded PDFs and identify exact duplicates using SHA-256; store originals in GridFS.
2. **Extract:** Parse page-aware Markdown and source information using LlamaParse.
3. **Chunk:** Split content with heading-aware LangChain splitters while retaining page/source references.
4. **Embed:** Generate Voyage AI vectors and store versioned retrieval artifacts in MongoDB Atlas.
5. **Summarize:** Use LangGraph to generate and validate five structured sections.
6. **Answer questions:** Retrieve relevant passages through vector and BM25 search, fuse rankings, generate an answer, and validate citations.

Processing jobs run independently of normal HTTP requests. Completed intermediate artifacts can be reused in supported retries.

## Technology Stack

| Area | Technology | Purpose |
|---|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS | Research dashboard and PDF workspace |
| Backend | Python, FastAPI, Pydantic | API endpoints and validation |
| PDF processing | LlamaParse, LangChain | Page-aware extraction and chunking |
| Embeddings | Voyage AI | Semantic representations |
| Storage and retrieval | MongoDB Atlas, GridFS, Vector Search, BM25 | PDFs, metadata, and hybrid search |
| AI orchestration | LangGraph, LangChain, OpenRouter | Summarization and question answering |
| Asynchronous processing | RabbitMQ | Background jobs and retries |
| Evaluation | Ragas, manual source review | Retrieval and answer-quality checks |
| Quality and deployment | pytest, Vitest, Playwright, Docker Compose, GitHub Actions | Testing and development workflows |

## Repository Structure

```text
Research-Assistant-for-PDFs/
├── frontend/                      # React application
├── backend/
│   ├── gateway/                   # FastAPI routes
│   ├── services/
│   │   ├── document_processor/    # Parsing, chunking, embeddings
│   │   ├── summary_service/       # LangGraph summaries
│   │   ├── rag_service/           # Retrieval and grounded QA
│   │   └── jobs/                  # Background processing
│   ├── shared/                    # Configuration and data models
│   └── tests/                     # Backend tests
├── evaluation/                    # Ragas datasets and reports
├── docs/                          # Architecture and setup guides
├── docker-compose.yml
├── .env.example
└── README.md
```

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

## API Overview

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/api/v1/documents` | Upload a PDF |
| `GET` | `/api/v1/documents/{id}/summary` | Read the saved summary |
| `GET` | `/api/v1/documents/{id}/chunks` | Read processed chunks |
| `POST` | `/api/v1/documents/{id}/chat` | Ask a paper-specific question |
| `GET` | `/api/v1/documents/{id}/chat/{conversation_id}` | Load conversation history |
| `DELETE` | `/api/v1/documents/{id}` | Delete a paper and associated records |

See the [API Guide](backend/gateway/README.md) for complete request and response contracts.

## Evaluation and Testing

RAG quality is evaluated **offline**, separately from user-facing chat, using a source-grounded benchmark that includes answerable and unanswerable questions. The evaluation considers **Context Precision, Context Recall, Faithfulness, Answer Relevancy, and Factual Correctness**. Semantic-only and hybrid retrieval can be compared, with manual checks for unsupported claims, citation quality, and false abstentions.

The results are not represented as a universal accuracy percentage. Published reports include failure cases and metric limitations; successful integration checks alone do not prove answer correctness across all research papers. See [Evaluation Methodology](evaluation/README.md) and the [QA Evaluation Report](evaluation/reports/2026-11-13-final-qa/README.md).


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

## Key Engineering Decisions

| Choice | Reason |
|---|---|
| Hybrid search with RRF | Balance semantic matching and precise technical terms |
| Document-scoped retrieval | Keep evidence tied to the selected paper |
| GridFS with MongoDB Atlas | Store original PDFs alongside document metadata |
| LangGraph summaries | Coordinate stateful, validated generation |
| RabbitMQ workers | Keep expensive AI processing outside request handling |
| Versioned artifacts | Reuse completed processing and support recovery |
| Citation validation | Reduce unsupported source references |
| Offline Ragas evaluation | Measure quality without increasing live chat latency |


## Documentation

Start with the [documentation index](docs/README.md) for current guides and dated verification records.

[Architecture](docs/architecture.md) · [Atlas Setup](docs/atlas-setup.md) · [Hybrid RAG](docs/hybrid-rag.md) · [Summarization](docs/structured-summary.md) · [PDF Citations](docs/pdf-citations.md) · [Background Jobs](docs/background-jobs.md) · [Evaluation](evaluation/README.md)
## Author

**Aravinthan Arrathikasarma**
AI Undergraduate — University of Moratuwa, Sri Lanka
[GitHub](https://github.com/arrathikan) · [LinkedIn](https://www.linkedin.com/in/aravinthan-arrathikasarma/)

---

*ResearchAI — Turning complex research papers into structured, source-grounded knowledge.*
