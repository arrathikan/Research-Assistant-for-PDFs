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
│   │   ├── App.tsx                         # Main application layout
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

### Docker application (Prompt 14)

Install Docker Desktop/Compose 2.24+, copy `.env.example` to `.env`, and configure
your existing Atlas URI and provider keys. From the project root:

```bash
docker compose up -d --build --wait
```

Open **http://localhost:3000**. Compose starts the built frontend, gateway,
RabbitMQ and processing workers together. This prevents a running UI from being
left without its API or workers. The local MongoDB service is optional; Atlas
remains the configured storage/search service.

For local storage-only testing:

```bash
MONGODB_URI=mongodb://mongodb:27017 docker compose --profile local up -d --build --wait
```

Local MongoDB does not provide Atlas vector/BM25 search. See [Docker setup,
configuration, safe smoke checks and operations](docs/deployment.md).

### Continuous integration

[GitHub Actions](https://github.com/arrathikan/Research-Assistant-for-PDFs/actions/workflows/ci.yml)
checks backend tests/lint with disposable MongoDB and RabbitMQ, frontend tests and
TypeScript/build, then a complete Docker smoke check. Normal CI has no provider
secrets and never runs a paid Ragas evaluation. See [CI checks, local reproduction
and limitations](docs/ci.md).

### Native development alternative

Use Python 3.11+ and Node.js 22. Keep the ignored `.env` configured for Atlas.
Start only the broker before launching the gateway, workers and Vite in separate
terminals:

```bash
docker compose up -d rabbitmq
```

### 4. Run Backend Gateway
```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.gateway.main:app --host 127.0.0.1 --port 8000 --reload
# Separate terminal, same backend environment:
python -m backend.services.jobs.main run
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

The Upload page opens a native dialog for PDF selection, validation, upload and
compact processing feedback. Done closes it after storage; the paper immediately
appears in the session library and continues processing independently. Closing an
active upload keeps its request alive while navigating within the app. Real status
polling, safe retries and SHA-256 duplicate handling remain; no percentages or
internal IDs are shown.

Dashboard paper menus provide Workspace, original PDF and a confirmed Delete Paper
action. `DELETE /api/v1/documents/{document_id}` removes owned files and scoped
research data with a worker deletion barrier and retryable partial cleanup.
Restart all workers with this version before using Delete. See [behavior, cleanup
contract, verification and limits](docs/document-actions-upload-dialog.md).


### Responsive page layout

Dashboard, Upload and Workspace now share a centered 1440px outer boundary,
including both existing navigation components. Gutters are 16px on mobile, 24px
on tablet and 32px on desktop. Upload headings, selection and status cards share
one focused 1024px column; summary/chat retain their readable 1200px boundary.
Dashboard uses its existing responsive statistics and auto-fit document grids,
so unused document columns collapse without adding metrics or changing data.

The app shell uses the available container width and dynamic viewport height.
Dashboard/Upload have one page scroll owner; Workspace keeps independent summary/
chat and PDF scrolling. An open PDF uses a 55/45 split from 768px and a full-screen
viewer on smaller displays. Shared minimum-width/height rules and wrapping prevent
page-level horizontal overflow. This refinement changes layout only. See
[application layout verification](docs/application-layout.md).


### Chat answer presentation

Answers use safe Markdown headings, lists, emphasis, code and comparison tables.
Verified inline citations open the existing PDF viewer. Supporting passages stay
inside one collapsed Sources section per answer. The PDF viewer keeps exact text
and verified-region highlighting, while page-only fallback is quiet and uses a
compact source toolbar. No raw retrieved chunks or internal retrieval metadata
are shown in normal chat.


Chat now routes factual, topical, analytical, comparison, follow-up and whole-paper
questions through the existing pipeline. Complete current summaries can be reused;
otherwise bounded section samples support a qualified overview. Explicit general
knowledge is labeled separately and carries no paper citations. Source-generation,
embedding-profile and exact-quote validation remain mandatory. See
[the architecture notes](docs/architecture.md#intent-sensitive-research-chat).

The measured nine-question research-assistant check is available in
[the intent evaluation report](evaluation/reports/2026-11-12-assistant/README.md).
The final run generated all 18 paired responses and all 60 applicable Ragas
values; assistant review still found five answers with incomplete citation
support. These results do not establish overall scientific-answer accuracy.


### Optional PDF workspace

The PDF is closed by default. Read the five-part summary or chat in a centered
column, then choose **View Original PDF** or click a source to open the existing
viewer. **Close PDF** restores the full-width workspace. Desktop/tablet use a
55/45 split; mobile opens a full-screen PDF with focus handling and Escape to
close. Page and zoom survive closing/reopening within the current document
session. Chat messages, drafts and summary content stay mounted.

Summary source buttons now use the same canonical citation resolver as chat.
Supporting passages are optional; missing exact highlights fall back quietly to
the cited page. See [workspace behavior and verification](docs/optional-pdf-workspace.md).


Workspace summary cards and the closed-PDF toolbar now share a centered 1200px
content limit. Summary paragraphs keep a 100ch line limit; chat bubbles have
separate readable limits while the conversation and input use the wider content
area. Desktop gutters are 32px. The optional PDF layout and state behavior are
preserved. See [measured layout verification](docs/optional-pdf-workspace.md).


### Refined research experience

ResearchAI now opens the existing Dashboard with an honest empty library. Upload
one real PDF to explore its saved summary or start a sourced conversation. The
shared warm brand/neutral controls, accessible document articles, keyboard tabs and
compact chat suggestions are consistent across pages. The optional PDF code loads
only when requested and retains its viewer state while hidden.

The library currently lasts for the App session; this frontend refinement adds no
listing API or cross-reload persistence. See [frontend guidance, changed files,
verification and limits](docs/frontend-experience.md).

### Final QA: summary recovery

The versioned summary workflow now requests short contiguous source quotes and
preserves strict quote validation. A live failed summary recovered through the
supported job retry without reparsing or re-embedding the paper. See the
[verified correction](docs/structured-summary.md#final-qa-quote-correction-2026-11-13).

### Browser verification

The approved Playwright development suite now checks real browser interactions,
PDF rendering and six responsive widths without paid API calls. Run
`npm run test:e2e` and `npm run typecheck` in `frontend`; see
[browser QA](docs/browser-qa.md) for installation, private screenshots and the
separate opt-in real-provider check.

### Final QA and interview demo (Prompt 15)

Use the [demo guide](docs/demo-guide.md) for setup, a six-minute walkthrough,
source questions and recovery. The [final QA report](docs/final-qa.md) records
474 backend tests, 140 proposed-frontend tests, 14 deterministic browser checks,
one live browser check and Docker smoke verification. The
[latest Ragas follow-up](evaluation/reports/2026-11-13-final-qa/README.md) contains
18 real responses and assistant source reviews, with 58 measured values and two
explicit metric errors. Citation quality, dependency advisories and public
production requirements remain documented follow-ups.

### Warm branding and reading workspace

The frontend now uses the supplied transparent logo, **#C6360A** brand accents,
compact paper-library rows and a continuous five-section reading layout. Upload,
chat and the optional PDF viewer keep their existing integration and state.
See [design changes and verification](docs/frontend-brand-redesign.md) for page
updates, logo provenance, responsive behavior and test scope.

### Reference dashboard and complete interaction theme

The Paper Library now has responsive sidebar navigation, four real metadata
statistics, filename search, status filtering and date/name sorting. The paper,
processing and ready illustrations come from the user's references; the selected
book-logo PNG is retained. Shared orange tokens cover primary/pressed buttons,
active tabs, citations and input focus while cards and secondary controls stay
neutral. Summary/Chat shortcuts respect data readiness. See the
[dashboard implementation and browser audit](docs/dashboard-reference-theme.md).
