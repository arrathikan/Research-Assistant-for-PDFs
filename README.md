# ResearchAI — AI Research Paper Assistant

ResearchAI is a modular, production-grade academic research paper assistant designed for researchers, graduate students, and software engineers. It automates academic paper comprehension through a predefined 5-section structured summary, conversational Hybrid RAG with citation generation, and an embedded PDF viewer featuring real-time source text highlighting.

---

## 📑 Core Capabilities

1. **Deterministic Structured Summarization (LangGraph):**
   - Automatically breaks down complex academic PDFs into 5 standard sections:
     - **Title, Authors, and Abstract**
     - **Problem Statement & Motivation**
     - **Methodology & Architecture**
     - **Key Empirical Results & Benchmarks**
     - **Conclusion & Future Directions**

2. **Conversational Hybrid RAG Chatbot:**
   - **Semantic Dense Search:** Powered by domain-specific Voyage AI embeddings (`voyage-3`).
   - **Lexical Sparse Search:** BM25 indexing targeting exact terminology, variable names, and mathematical symbols.
   - **Reciprocal Rank Fusion (RRF):** Merges dense and sparse candidates to maximize both recall and precision.
   - **Guardrails:** Grounded answers only; gracefully abstains when queries fall outside the paper's scope.

3. **Interactive PDF Viewer with Citation Highlighting:**
   - Built on React-PDF / PDF.js.
   - Every response provides source citation chips (e.g. `[Page 4, Section 3.2]`).
   - Clicking a citation scrolls the embedded viewer directly to the source page and highlights the supporting passage.

4. **Rigorous Offline Ragas Evaluation:**
   - Complete evaluation suite decoupled from live user requests.
   - Separate measurement of Retrieval Quality (*Context Precision*, *Context Recall*) and Generation Quality (*Faithfulness*, *Answer Relevancy*, *Factual Correctness*).
   - Curated benchmark dataset containing both answerable and unanswerable questions to test abstention.

---

## 🛠️ Technology Stack

| Domain | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS | Responsive split-view workspace |
| **PDF Viewer** | React-PDF / PDF.js | Highlighting overlay, canvas rendering, text layer |
| **API Gateway** | FastAPI, Pydantic v2, Uvicorn | Central REST API and request routing |
| **Message Broker** | RabbitMQ | Asynchronous job queues for heavy extraction and summarization |
| **PDF Extraction** | LlamaParse | Academic layout parsing with page tracking |
| **Text Chunking** | LangChain Text Splitters | Markdown- and header-aware chunk segmentation |
| **Embeddings** | Voyage AI (`voyage-3`) | Dense vector representations for technical literature |
| **Database & Storage** | MongoDB Atlas + GridFS | Structured metadata, chunk vectors, raw PDF binaries |
| **Hybrid Search** | Dense Vector + BM25 + RRF | Multimodal text retrieval with rank fusion |
| **Summarizer** | LangGraph | Stateful deterministic extraction graph |
| **Chat Engine** | LangChain + Configurable LLM | Conversational QA with verifiable citations |
| **RAG Evaluation** | Ragas + Manual Benchmarking | Automated evaluation suite and failure tracking |
| **Testing** | pytest + Vitest | Unit, integration, and UI testing |
| **Infrastructure** | Docker Compose | Local multi-service orchestration |

---

## 📁 Monorepo Project Structure

```
.
├── frontend/                               # React + Vite + Tailwind CSS client
│   ├── src/
│   │   ├── components/                     # Navbar, SplitView, UI components
│   │   ├── types/                          # TypeScript contracts mirroring backend
│   │   ├── App.tsx                         # Main split-screen application layout
│   │   └── main.tsx                        # Application mount
│   ├── package.json                        # Frontend dependency definitions
│   └── vite.config.ts                      # Vite build configuration
│
├── backend/                                # Python FastAPI services & workers
│   ├── gateway/                            # Central API Gateway service
│   │   ├── main.py                         # Health endpoints and route orchestrator
│   │   └── README.md                       # Gateway architecture documentation
│   ├── services/
│   │   ├── document_processor/             # PDF extraction & chunking worker
│   │   │   ├── main.py                     # LlamaParse & RabbitMQ consumer
│   │   │   └── README.md
│   │   ├── summary_service/                # LangGraph 5-section summarizer
│   │   │   ├── main.py                     # Deterministic state machine
│   │   │   └── README.md
│   │   └── rag_service/                    # Hybrid RAG & citation engine
│   │       ├── main.py                     # Voyage AI + BM25 + RRF retriever
│   │       └── README.md
│   ├── shared/                             # Cross-cutting configurations & contracts
│   │   ├── config.py                       # Pydantic BaseSettings (.env loading)
│   │   ├── models.py                       # Shared Pydantic data schemas
│   │   ├── logging.py                      # Standardized structured logging
│   │   └── README.md
│   ├── tests/                              # Backend pytest test suite
│   │   ├── test_shared_models.py           # Domain schema validation tests
│   │   ├── test_gateway_health.py          # API Gateway health tests
│   │   └── test_evaluation_schemas.py      # Evaluation schema & benchmark tests
│   ├── pyproject.toml                      # Modern Python packaging configuration
│   └── requirements.txt                    # Pinned backend dependencies
│
├── evaluation/                             # Offline Ragas benchmarking subsystem
│   ├── schemas.py                          # Evaluation sample & report data models
│   ├── benchmark_dataset.json              # Curated queries (answerable & unanswerable)
│   ├── README.md                           # Ragas evaluation rules & guidelines
│   └── reports/                            # Versioned evaluation benchmark reports
│
├── docs/                                   # Architectural & operational documentation
│   ├── architecture.md                     # System design, data flows, and schemas
│   └── development-roadmap.md              # Staged development plan & progress tracker
│
├── docker-compose.yml                      # Containerized MongoDB & RabbitMQ services
├── .env.example                            # Configuration environment template
├── .gitignore                              # Git exclusion rules
├── AGENTS.md                               # Project engineering & mentor rules
└── README.md                               # Project introduction and overview
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ & npm

### 2. Environment Configuration
Copy `.env.example` to `.env` and configure your API keys:
```bash
cp .env.example .env
```

### 3. Start Infrastructure Services
Launch MongoDB and RabbitMQ using Docker Compose:
```bash
docker compose up -d
```

### 4. Run Backend Gateway
```bash
pip install -r backend/requirements.txt
uvicorn backend.gateway.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run Frontend Development Server
```bash
cd frontend
npm install
npm run dev
```

### 6. Run Test Suite
```bash
PYTHONPATH=. pytest backend/tests/
```

---

## 📖 Guidelines & Architecture

- **[AGENTS.md](AGENTS.md):** Coding mentor persona, 20 automatic Git rules, and 16 Ragas evaluation principles.
- **[docs/architecture.md](docs/architecture.md):** Detailed system architecture, data flows, and MongoDB collection schemas.
- **[docs/development-roadmap.md](docs/development-roadmap.md):** 10-stage implementation roadmap and increment log.

## Current implementation status

Prompts 0–2 supplied the existing scaffolding and frontend. Prompt 3 gateway
contracts, centralized errors, JSON logging and CORS checks are implemented; see
[the gateway guide](backend/gateway/README.md) for verification commands. The
capabilities described above are the target architecture; upload, storage and AI
processing are not yet implemented end to end. Health checks indicate gateway
liveness only. The original prompt progression is tracked in
[the roadmap](docs/development-roadmap.md).

### MongoDB setup

Prompt 4 adds explicit MongoDB connection and index initialization. After
configuring `MONGODB_URI`, `MONGODB_DB_NAME`, and `MONGODB_TIMEOUT_MS`, run
`python -m backend.shared.database` from the project root. See
[the storage guide](backend/shared/README.md) for permissions and lifecycle details.

Prompt 4 now includes GridFS persistence and retrieval, validated metadata, and
SHA-256 uniqueness under concurrent writes. These are internal storage helpers;
HTTP upload routes remain Prompt 5. Offline unit tests use mocked drivers.
Opt-in live tests create/drop only uniquely named disposable databases:

```bash
RESEARCHAI_TEST_MONGODB_URI=mongodb://localhost:27017 python -m pytest backend/tests -m integration -q
```

See the storage guide for non-atomic write recovery limits and complete checks.
Atlas-specific DNS, TLS, credentials, and network rules require verification
against your own configured test cluster; local integration results do not
prove Atlas connectivity.

### PDF upload validation (Prompt 5)

Uploads use the configurable `MAX_UPLOAD_SIZE_BYTES` (default 26214400 bytes).
The validator checks extension, MIME, header/trailer, PDF structure and page tree
using pypdf. Corrupt, encrypted, empty or zero-page PDFs are rejected. Browser
MIME may be empty or `application/octet-stream`, but the bytes must still pass
PDF validation. Filenames are reduced to a basename. Strict validation can reject
PDFs that a viewer might repair; it is not malware scanning or content extraction.

The gateway now exposes `POST /api/v1/documents` (compatibility alias
`/documents/upload`), metadata/status GET routes, and an original-PDF GET route.
New uploads return 201; exact duplicates return 200 and the existing record.
Documents remain `PENDING` until later processing stages are implemented.
See [gateway API details](backend/gateway/README.md) for commands, errors and limits.

### Local verification

Upload, duplicate detection, invalid-file rejection, status and exact original
PDF download have been verified with isolated local MongoDB and the browser UI.
The backend suite passed 87 tests; the current frontend working checkout passed
22 tests and a full production build. See [verification details](docs/verification-report.md)
for scope, local workspace status and features still awaiting implementation.

### Page-aware PDF extraction (Prompt 6)

Extraction contracts now preserve page-specific Markdown, headings/tables, source
elements and available coordinates. Missing coordinates support page-navigation
fallback; page numbers are never inferred from an incomplete parser response.

Prompt 6 uses LlamaParse v2 through the provider's supported `llama-cloud` SDK.
Configure `LLAMA_CLOUD_API_KEY`, `LLAMA_PARSE_TIMEOUT_SECONDS`,
`LLAMA_PARSE_TIER` and `LLAMA_PARSE_VERSION`; see the
[document processor guide](backend/services/document_processor/README.md).
Source boxes retain their documented coordinate units and nested relationships.

GridFS extraction now records `parsing_status` and `parsed_at`, with versioned
per-page/source persistence. Successful parsing leaves the overall document
`PENDING` for later stages; it does not imply embeddings, summaries or chat are
ready. Failed or interrupted attempts never publish incomplete page results.

Prompt 6 extraction is available through an explicit CLI after configuring the
LlamaParse key and the database containing the uploaded file:

```bash
python -m backend.services.document_processor.main DOCUMENT_ID
curl http://localhost:8000/api/v1/documents/DOCUMENT_ID/parsed
```

The parsed-result endpoint is read-only; uploads do not invoke paid parsing
automatically. Chunking and queue dispatch remain later stages. Local MongoDB
verification passed 141 tests with one paid provider smoke test skipped. Live
cloud parsing was not run because no API key was configured. See the
[extraction guide](backend/services/document_processor/README.md) for configuration,
status transitions, recovery, source coordinates and opt-in live verification.

### Markdown-aware chunking (Prompt 7)

LangChain header-aware and recursive splitters now create bounded research
chunks with heading paths, stable IDs, explicit page evidence spans and source
references. Configure `CHUNK_SIZE=1200` and `CHUNK_OVERLAP=150` (character counts,
not tokens). Overlap must be nonnegative and smaller than the chunk size.
Unrelated sections remain separate; section continuation may span PDF pages.

Chunk storage now keeps immutable generations and publishes only complete sets.
Changing configuration preserves older output. Metadata includes chunking_status
and chunked_at. The original unique chunk index can be upgraded automatically
only while its collection is empty; populated legacy data requires review.

Run chunking after the document has a published parse:

```bash
python -m backend.services.document_processor.chunk_cli DOCUMENT_ID
curl http://localhost:8000/api/v1/documents/DOCUMENT_ID/chunks
```

This stage is local and needs no provider keys. The read endpoint returns only
complete chunks for the current parsed version. Local MongoDB verification
passed 178 tests with one paid parser test skipped. See the
[chunking guide](docs/markdown-chunking.md) for page/source mapping, settings,
versioned storage, index compatibility and recovery. Embeddings are Prompt 8.

### Voyage embeddings (Prompt 8)

The Voyage adapter distinguishes document and query inputs, disables silent
truncation, validates dimensions/finite nonzero vectors, and applies bounded
batching/retry guards. Existing voyage-3/1024 configuration is preserved;
voyage-4 and its supported dimensions are explicit configuration choices.

Embed a previously parsed and chunked PDF explicitly (may consume Voyage credits):

```bash
python -m backend.services.document_processor.embed_cli DOCUMENT_ID
```

Completed content/profile vectors are reused across retries and documents. Embedding
completion leaves the document `PENDING` for the later summary stage. The original
chunks and their page/source metadata are preserved in searchable snapshots.

### Configured AI providers

The local environment and template use OpenRouter for future completion calls,
Voyage `voyage-4-lite` with 1024 dimensions, and LlamaParse `agentic` parsing.
The primary, inexpensive and vision model roles, environment variable aliases,
and remaining integration work are described in the
[provider configuration guide](docs/provider-configuration.md).

### Structured summaries (Prompt 9)

Summary output contracts and the OpenRouter completion adapter now enforce
explicit missing information and source references. See the
[summary guide](docs/structured-summary.md) for configuration and current scope.

The summary LangGraph now extracts bounded research windows, validates evidence,
repairs invalid output at most twice, and combines long-paper notes without
silently dropping chunks. Versioned persistence and the frontend summary connection are implemented.

Generate a parsed/chunked document summary with
`python -m backend.services.summary_service.main DOCUMENT_ID`. Retrieve the saved
result through `GET /api/v1/documents/{id}/summary`; this read never calls the LLM.

The five summary cards now read saved results with loading, waiting and error
states, and display source pages/quotes. The real OpenRouter summary smoke test
passed on synthetic input. See the [summary guide](docs/structured-summary.md)
for commands, test scope and remaining work.

After upload, View summary opens the read-only summary panel even while the
document is waiting for embeddings. Generation remains an explicit CLI job
until background orchestration is implemented.

Embedding storage is now available through the explicit embedding command above.
Successful cached batches survive retries; current summaries and embeddings can
finish in either order. Atlas index/search verification remains separate.

### Hybrid RAG (Prompt 10)

The document-scoped Atlas vector/BM25 retriever and Python rank fusion are
implemented. See [hybrid RAG setup](docs/hybrid-rag.md) for explicit index creation,
settings and verification limits. Atlas connectivity and the vector/BM25 indexes have now been verified live;
see the verification report below for the exact scope.

The LangChain answer chain now validates claim-level source quotes and abstains
when evidence is insufficient. Internal typed traces support later offline Ragas
evaluation; no evaluation runs during ordinary chat requests.

The chatbot API now supports document-scoped conversations and saved history:
`POST /api/v1/documents/{id}/chat` and
`GET /api/v1/documents/{id}/chat/{conversation_id}`. Successful turns are saved
atomically; private retrieval traces are excluded from public responses.

The React chatbot now sends real questions, recovers saved conversations and
shows source quotes and unavailable/unsupported states. A live OpenRouter answer
check passed on synthetic text. The separate live Atlas hybrid-retrieval check also passed on synthetic input.
See [the RAG guide](docs/hybrid-rag.md) for setup and opt-in checks.

New to Atlas? Follow the [project setup guide](docs/atlas-setup.md), then keep your
connection string only in the ignored local `.env`.


Atlas verification (2026-11-11): the real Voyage → Atlas vector/BM25 → OpenRouter
integration test **passed** with verified document-scoped citations. Both
application search indexes are queryable. Backend regression checks: **303 passed,
4 optional live tests skipped**; the live Atlas check was enabled and run separately.
See [the verification report](docs/atlas-verification.md). This establishes the
synthetic workflow, not a scientific-summary/RAG accuracy benchmark.

### PDF citations (Prompt 11)

Citations now preserve source geometry and generation metadata. A deterministic
resolver checks their document, page, quote and active source version before
navigation. Chat citation buttons now jump to the uploaded PDF in React-PDF,
with text highlights, confirmed region highlights or an explicit page-only fallback.
Page navigation, zoom and mobile source switching are available. See [PDF citations](docs/pdf-citations.md) for the contract and scope.


Prompt 11 verification: **325 backend tests passed, 4 optional live checks skipped**;
**69 frontend tests passed** in an isolated commit copy, plus production build.
Browser QA confirmed two-line PDF highlights, zoom, repeated source navigation,
page-only fallback and mobile navigation on a synthetic PDF with simulated
provider responses. See the [citation demo and scope](docs/pdf-citations.md#try-it-locally).


### Background processing (Prompt 12)

Uploads now save durable processing jobs. RabbitMQ workers automatically run PDF
parsing, Markdown chunking, embeddings and the five-section summary. The upload
screen shows progress and retry states, then enables opening the ready workspace.

From the project root with the backend environment activated:

```bash
docker compose up -d rabbitmq
python -m backend.services.jobs.main run
```

Run these workers independently of the gateway. See [background jobs](docs/background-jobs.md)
for configuration, the processing status/retry API, dead letters and reviewed
interrupted-job recovery. Existing completed artifacts are reused. Unrequested
legacy documents are not automatically processed.

Real RabbitMQ/disposable MongoDB verification: **366 backend tests passed,
4 optional live provider checks skipped**. Paid providers were simulated for the
job integration checks; no Ragas accuracy scores are claimed here.

Isolated frontend verification: **75 tests passed** and production build passed.


Prompt 13 implements [offline Ragas evaluation](evaluation/README.md), with a
20-case source-grounded dataset, paired hybrid/semantic collection, five metrics,
validated JSON/Markdown reports and result-bound manual reviews. At the user's
request, source and generated-answer checks were performed by Codex and are
explicitly recorded as assistant reviews.

The [first measured baseline](evaluation/reports/2026-11-12/README.md) covers all
20 questions with both strategies. It records real generation failures, false
abstentions and incorrect answers; metric coverage and limitations remain visible.
The evaluation workflow is implemented; the baseline exposes RAG quality issues
that still need improvement. Final backend checks: **410 passed, 4 optional live
checks skipped**. Evaluation never runs during ordinary chat requests.


### Upload interface

The upload page uses a compact file card with readable upload, queued, processing,
ready and failure states. Status comes from the existing processing and document
APIs; the interface does not estimate percentages. PDF access unlocks after
storage, chat requires completed embeddings, and summary access requires a
successful read of the current saved summary. Ready requires confirmed document
and background-job completion plus the available summary and embeddings.

Retry/start controls follow the backend's supported job states. Choosing another
paper clears the previous result and cancels its status updates. Drag-and-drop,
PDF validation and duplicate handling remain supported. The card and navigation
adapt to narrow screens, with keyboard controls, visible focus and live status
announcements. No processing APIs or worker logic were changed.


### Responsive page layout

Dashboard, Upload and Workspace share a centered 1152px page container and
matching navigation gutters. The upload heading, form and result cards share
one readable column capped at 768px; competing 576px inner limits were removed.
Dashboard uses an auto-fit document grid so two papers do not reserve a third
empty desktop column.

The app shell uses the available container width and dynamic viewport height.
Dashboard/Upload have one page scroll owner; Workspace keeps independent summary/
chat and PDF scrolling. Below the desktop breakpoint, the visible workspace pane
uses the full column. Shared minimum-width/height rules and wrapping prevent
page-level horizontal overflow. This refinement changes layout only.
