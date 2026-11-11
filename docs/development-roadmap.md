# ResearchAI Development Roadmap

This roadmap breaks down the complete development of **ResearchAI — AI Research Paper Assistant** into sequential, test-driven stages and manageable increments.

---

## Roadmap Overview

| Stage | Name | Key Deliverable | Status |
|---|---|---|---|
| **Stage 0** | Foundation & Repository Setup | Rules, architecture, roadmap, Git workflow | **Completed** |
| **Stage 1** | Containerized Infrastructure & Scaffolding | Docker Compose, FastAPI skeleton, Vite React setup | **Completed** |
| **Stage 2** | PDF Upload, Deduplication & Storage | SHA-256 detection, MongoDB GridFS, upload validation | Not Started |
| **Stage 3** | Ingestion & Markdown Parsing Worker | RabbitMQ queues, LlamaParse, page-aware chunking | Not Started |
| **Stage 4** | Embeddings & Hybrid Vector/Keyword Store | Voyage AI embeddings, Atlas Vector Search, BM25 | Not Started |
| **Stage 5** | Automated Structured Summary Workflow | LangGraph state graph (5-part academic summary) | Not Started |
| **Stage 6** | Conversational Hybrid RAG & Citations | Semantic + BM25 + RRF, LangChain QA, citation linking | Not Started |
| **Stage 7** | Frontend UI & Interactive PDF Viewer | React-PDF/PDF.js, split view, citation highlighting | Not Started |
| **Stage 8** | Evaluation, Testing & Quality Assurance | Ragas evaluation, pytest test suite, Vitest suite | Not Started |
| **Stage 9** | CI/CD Pipeline & Final Polish | GitHub Actions CI, complete documentation | Not Started |

---

## Stage 0: Foundation & Repository Setup (Current)

- [x] **Increment 0.1: Repository Inspection & Agent Rules**
  - Inspect repository structure, branch state, and remote authentication.
  - Create `AGENTS.md` containing engineering standards, Git rules, tech stack boundaries, and reporting format.
- [x] **Increment 0.2: Architecture & Roadmap Documentation**
  - Create `docs/architecture.md` detailing system topology, microservices, and data flows.
  - Create `docs/development-roadmap.md` detailing stages, increments, and deliverables.
- [x] **Increment 0.3: Git Workflow & Environment Configuration**
  - Create `.gitignore` to prevent secret leaks, `.env`, binaries, and build artifacts from entering Git.
  - Create `.env.example` defining all required configuration variables.
  - Update `README.md` to reflect project overview, setup, and roadmap.
  - Commit and push to feature branch `stage-0/foundation`.

---

## Stage 1: Containerized Infrastructure & Scaffolding

- [x] **Increment 1.1: Docker Compose & Infrastructure Services**
  - Create `docker-compose.yml` for RabbitMQ and MongoDB with health checks and persistent volumes.
  - Configure RabbitMQ management dashboard and standard networks.
- [x] **Increment 1.2: Backend Core Scaffolding (Gateway & Microservices)**
  - Scaffold microservices monorepo: `backend/gateway/`, `backend/services/`, `backend/shared/`, `backend/tests/`.
  - Implement health check endpoints (`GET /health`, `GET /api/v1/health`) and CORS middleware.
  - Implement centralized `Settings` using Pydantic `BaseSettings` and structured logging.
  - Add pytest test suite covering domain models, schemas, and gateway health.
- [x] **Increment 1.3: Frontend Core Scaffolding (React + Vite + Tailwind)**
  - Scaffold `frontend/` using Vite, React 18+, TypeScript, and Tailwind CSS.
  - Implement base layout (`Navbar`, `SplitView`, and responsive container).
  - Define TypeScript domain contracts strictly matching backend schemas.
- [x] **Increment 1.4: Evaluation Subsystem Scaffolding (Ragas & Benchmark)**
  - Scaffold `evaluation/` directory with Pydantic schemas, benchmark dataset, and report directories.
  - Add deterministic unit tests validating benchmark dataset and evaluation contracts.

---

## Stage 2: PDF Upload, Deduplication & Storage

- [ ] **Increment 2.1: PDF Upload Validation & Storage Layer**
  - Create Pydantic schemas for upload responses.
  - Implement file validation: MIME type check (`application/pdf`) and size check (max 25MB).
  - Set up MongoDB GridFS driver for storing raw PDF byte streams.
- [ ] **Increment 2.2: SHA-256 Deduplication Logic**
  - Calculate SHA-256 checksum from uploaded file stream.
  - Query MongoDB `documents` collection for existing checksum before GridFS insertion.
  - Return existing document record immediately if duplicate is detected, preventing redundant processing.
- [ ] **Increment 2.3: Document Metadata Persistence & Status Tracking**
  - Store document record with status `PENDING`.
  - Implement status polling endpoint (`GET /api/v1/documents/{id}/status`).
  - Unit tests covering duplicate upload, invalid MIME types, and oversized files.

---

## Stage 3: Ingestion & Markdown Parsing Worker

- [ ] **Increment 3.1: RabbitMQ Messaging Producer & Worker Service**
  - Implement asynchronous message publisher in FastAPI on successful PDF upload.
  - Create dedicated worker service listening to `document_ingestion_queue`.
  - Configure acknowledgement, retry backoff, and dead-letter queue (`document_dlq`).
- [ ] **Increment 3.2: LlamaParse Integration with Page Preservation**
  - Integrate LlamaParse client to extract clean Markdown from raw PDF stream.
  - Ensure extracted Markdown preserves explicit page separators (`--- Page X ---`) and header structures.
- [ ] **Increment 3.3: Markdown-Aware Chunking (LangChain)**
  - Implement `MarkdownHeaderTextSplitter` + `RecursiveCharacterTextSplitter`.
  - Attach page number, section title, and chunk index metadata to every chunk.
  - Unit tests verifying chunk boundaries and metadata preservation across page transitions.

---

## Stage 4: Embeddings & Hybrid Vector/Keyword Store

- [ ] **Increment 4.1: Voyage AI Embeddings Integration**
  - Implement Voyage AI client service using `voyage-3` or `voyage-large-2-instruct`.
  - Batch chunk embeddings with rate limit protection and retry logic.
- [ ] **Increment 4.2: MongoDB Atlas Vector Search Indexing**
  - Persist chunks with their vector embeddings into MongoDB `chunks` collection.
  - Configure MongoDB Atlas Vector Search index definition (cosine similarity, dimensions).
- [ ] **Increment 4.3: BM25 Sparse Keyword Indexing**
  - Implement BM25 index over chunk text for lexical/keyword search.
  - Create retrieval benchmarks comparing pure dense vs pure sparse recall.

---

## Stage 5: Automated Structured Summary Workflow (LangGraph)

- [ ] **Increment 5.1: LangGraph Workflow Design & State Definition**
  - Define `SummaryState` Pydantic model and state graph.
  - Configure transitions between extraction nodes.
- [ ] **Increment 5.2: 5-Section Academic Summary Generation**
  - Node 1: Title, Authors, and Abstract extraction.
  - Node 2: Problem Statement extraction.
  - Node 3: Methodology extraction.
  - Node 4: Key Results & Findings extraction.
  - Node 5: Conclusion & Limitations extraction.
- [ ] **Increment 5.3: Schema Validation & MongoDB Persistence**
  - Validate output against `StructuredSummary` Pydantic model.
  - Store summary in MongoDB `summaries` collection and update document status to `READY`.
  - Implement `GET /api/v1/documents/{id}/summary` endpoint with unit tests.

---

## Stage 6: Conversational Hybrid RAG & Citations

- [ ] **Increment 6.1: Hybrid Retriever with Reciprocal Rank Fusion (RRF)**
  - Implement parallel retrieval: Top-K dense vectors (Voyage AI) + Top-K BM25 keywords.
  - Implement Reciprocal Rank Fusion ($k=60$) to re-rank and select top-N unified chunks.
- [ ] **Increment 6.2: LangChain Conversational Chain with Source Citations**
  - Implement conversational chain retaining short-term chat context.
  - System prompt enforcing citation syntax: `[Source: Page P, Chunk C]`.
  - Structure API response with answer text and array of source citation references.
- [ ] **Increment 6.3: Unsupported Question & Out-of-Scope Fallbacks**
  - Implement guardrail prompt preventing hallucination on questions not answered by the paper.
  - Test suite covering valid queries, ambiguous queries, and out-of-scope queries.

---

## Stage 7: Frontend UI & Interactive PDF Viewer

- [ ] **Increment 7.1: Document Upload & Status Component**
  - Drag-and-drop file upload zone with file validation and progress bar.
  - Polling status badge tracking ingestion pipeline phases.
- [ ] **Increment 7.2: Structured Summary Display**
  - Clean, readable presentation of the 5 summary sections (Title/Authors/Abstract, Problem, Methodology, Results, Conclusion).
  - Collapsible panels or tabbed views with copy-to-clipboard actions.
- [ ] **Increment 7.3: Interactive React-PDF / PDF.js Viewer**
  - Embed PDF viewer with page navigation, zoom controls, and text layer rendering.
  - Expose programmatic `jumpToPage(pageNumber)` and `highlightText(snippet)` APIs.
- [ ] **Increment 7.4: Chat Interface with Clickable Citation Links**
  - Chat message feed with user and assistant bubbles.
  - Clickable citation pills that immediately scroll the PDF viewer to the cited page and highlight the relevant passage.

---

## Stage 8: Evaluation, Testing & Quality Assurance

- [ ] **Increment 8.1: Backend Integration & End-to-End Test Suite**
  - Comprehensive pytest test suite for FastAPI endpoints, RabbitMQ queues, and LangGraph workflow.
- [ ] **Increment 8.2: Frontend Component & Integration Test Suite**
  - Vitest + React Testing Library tests for upload, summary render, chat, and citation click handlers.
- [ ] **Increment 8.3: Ragas Evaluation Benchmark & Manual Verification**
  - Implement curated benchmark dataset containing both answerable and unanswerable/out-of-scope questions.
  - Implement deterministic unit tests for evaluation dataset schema validation and report generation.
  - Integrate Ragas modern collections-based API (`EvaluationDataset`, `evaluate()`) evaluating retrieval (Context Precision, Context Recall) and generation (Faithfulness, Answer Relevancy, Factual Correctness) separately.
  - Implement comparative benchmarking harness comparing Hybrid Retrieval (Vector + BM25 + RRF) vs Semantic-only search.
  - Perform manual cross-verification and record reproducible reports in `evaluations/reports/`.

---

## Stage 9: CI/CD Pipeline & Final Polish

- [ ] **Increment 9.1: GitHub Actions CI Workflow**
  - Configure `.github/workflows/ci.yml` running linting, formatting, backend tests, and frontend tests on push and PR.
- [ ] **Increment 9.2: Complete Documentation & Deployment Polish**
  - Verify Docker Compose full-stack startup (`docker-compose up --build`).
  - Finalize README setup instructions, troubleshooting guide, and demo video / screenshots guide.

## Development prompt tracking (original 0–15 plan)

The stage numbers above group the architecture differently from the original
development prompts. Prompts 0–2 are the existing rules, scaffolding and frontend.

- [x] Prompt 3.1: Gateway contracts, errors, JSON logging, CORS and backend tests.
- [ ] Prompt 3.2: Frontend health connection indicator.
- [x] Prompt 4: MongoDB Atlas-compatible / GridFS storage (Atlas deployment verification pending).
- [x] Prompt 5: PDF upload, validation, deduplication and local verification.
- [x] Prompt 6: LlamaParse v2 extraction, status, persistence and local verification.
- [ ] Prompts 7–15: Chunking, embeddings, summary, hybrid RAG,
  citations, jobs, offline Ragas, deployment and final live QA.

Prompt 3.1 verification: 17 backend tests passed. Health does not imply external
service readiness. Existing uncommitted frontend work was preserved.

### Prompt 4 increments

- [x] 4.1: Explicit PyMongo lifecycle, bounded connections and collection indexes.
- [x] 4.2: GridFS persistence, validated metadata and concurrent deduplication.
- [x] 4.3: Optional isolated live storage tests and setup documentation.

Prompt 4 verification (2026-11-10): 49 backend tests passed against a temporary
loopback-only MongoDB 8.2.0, including all 3 live tests. Without the test URI,
46 passed and the 3 live tests were skipped. PyMongo 4.19.0 and Python 3.13.5
were used. Ruff lint/format checks passed for the six Prompt 4 Python files.
Atlas connectivity and frontend tests were not run for this storage stage.

### Prompt 5: PDF upload and duplicate detection

- [x] 5.1: Bounded validation of filename, MIME, PDF structure and page count.
- [x] 5.2: Upload, metadata/status and original-PDF API routes.
- [x] 5.3: Real frontend success/duplicate/failure states and upload tests.
- [x] 5.4: Isolated API/database integration verification and demo commands.

The user approved pypdf for upload validation. Parsing/extraction remains Prompt 6.

### Upload verification follow-up (2026-11-10)

- Fixed initial-response timestamp precision to match persisted BSON dates.
- Full backend suite with temporary local MongoDB: **87 passed**, including
  upload, duplicate, status, original-file retrieval and concurrent requests.
- Added the live upload integration tests to version control; private PDF data
  remains outside the repository. Atlas deployment verification is still pending.

Local browser verification (2026-11-11): upload, duplicate detection, invalid-file
rejection and recovery passed. Original downloads matched bytes/SHA-256; one
metadata record and file remained. Full local frontend build and 22 tests passed.
See [verification report](verification-report.md) for exact scope and limitations.

### Prompt 6: LlamaParse extraction

- [x] 6.1: Page-aware Markdown and source-element normalization contracts.
- [x] 6.2: Supported LlamaParse v2 SDK adapter and complete source metadata.
- [x] 6.3: GridFS orchestration and versioned parse persistence.
- [x] 6.4: CLI, integration checks, opt-in paid live test and documentation.

Coordinate metadata is preserved when valid. Missing/unknown coordinate systems
require page navigation fallback; layout boxes are not guessed for text items.

Prompt 6 verification (2026-11-11): **141 passed, 1 skipped** against isolated
MongoDB with provider calls mocked. The skipped test is the opt-in paid provider
smoke test; no LlamaParse API key was configured. Offline: **131 passed, 11 skipped**.
CLI help and SDK response-model tests passed. RabbitMQ dispatch and automatic
upload-to-parse triggering remain later stages.
