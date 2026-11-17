
# ResearchAI — AI-Powered Research Paper Assistant

**Understand research papers faster. Ask questions with confidence. Verify every answer against its source.**

ResearchAI is a full-stack, AI-powered research assistant that transforms complex academic PDF documents into structured summaries and interactive, citation-grounded conversations.

Built with **React, FastAPI, LangGraph, Hybrid RAG, MongoDB Atlas, and RabbitMQ**, ResearchAI combines intelligent document processing, retrieval-augmented generation, and source verification in a unified research workspace.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-TypeScript-149ECA?logo=react&logoColor=white)](https://react.dev/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

**[Repository](https://github.com/arrathikan/Research-Assistant-for-PDFs)** · **[Architecture](docs/architecture.md)** · **[Demo Guide](docs/demo-guide.md)** · **[Evaluation](evaluation/README.md)**

---

## Overview

Academic research papers often contain dense technical explanations, complex methodologies, and extensive experimental results. Understanding these documents requires significant time, while conventional AI chatbots may produce answers without reliable evidence.

ResearchAI addresses these challenges by providing a document-centered research environment where users can upload papers, explore standardized summaries, ask natural-language questions, and navigate directly to supporting evidence inside the original PDF.

### Key Capabilities

- **Structured AI Summarization:** Generate consistent, five-section research paper summaries.
- **Hybrid Retrieval-Augmented Generation:** Combine dense semantic retrieval and BM25 keyword search for document-grounded question answering.
- **Verifiable Citations:** Navigate directly from generated answers to supporting PDF pages and highlighted passages.
- **Automated Document Processing:** Process uploaded documents through durable background jobs with retry and recovery handling.
- **Research Workspace:** Manage papers, search the document library, and interact with research content through a responsive interface.
- **RAG Quality Evaluation:** Evaluate retrieval and answer generation using Ragas benchmarks and source-based manual reviews.

---

## System Architecture

ResearchAI uses a modular architecture that separates the user interface, API layer, background processing, document storage, and AI workflows.

```mermaid
flowchart TD
    U["Researcher"] --> UI["React + TypeScript Frontend"]
    UI --> API["FastAPI Gateway"]

    API --> DB[("MongoDB Atlas + GridFS")]
    API --> JOB["Durable Processing Jobs"]
    JOB --> MQ["RabbitMQ"]
    MQ --> WORKER["Background Workers"]

    WORKER --> PARSE["LlamaParse Extraction"]
    PARSE --> CHUNK["Markdown-Aware Chunking"]
    CHUNK --> EMBED["Voyage AI Embeddings"]
    EMBED --> DB

    WORKER --> SUMMARY["LangGraph Summarization"]
    SUMMARY --> DB

    UI --> CHAT["Research Chat Interface"]
    CHAT --> API
    API --> RAG["Hybrid RAG Pipeline"]

    RAG --> VECTOR["Atlas Vector Search"]
    RAG --> BM25["BM25 Search"]
    VECTOR --> RRF["Reciprocal Rank Fusion"]
    BM25 --> RRF
    RRF --> LLM["LLM Answer Generation"]
    LLM --> CITE["Citation Verification"]
    CITE --> UI
```

### Document Processing Workflow

1. **Upload and validation:** A PDF is checked for file format, integrity, size, and duplicate content.
2. **Secure document persistence:** The original PDF is stored in MongoDB GridFS with associated metadata.
3. **Background execution:** RabbitMQ workers coordinate extraction, chunking, embedding generation, and summarization.
4. **Content extraction:** LlamaParse extracts page-aware Markdown and available document structure.
5. **Intelligent chunking:** LangChain splitters preserve headings, relevant context, page references, and source metadata.
6. **Vectorization:** Voyage AI generates semantic embeddings, which are persisted for retrieval.
7. **Structured summarization:** LangGraph coordinates source-grounded summary generation and validation.
8. **Research interaction:** Users explore saved summaries and ask questions through the Hybrid RAG chatbot.

Completed intermediate processing artifacts can be reused during supported retries, reducing unnecessary provider calls and repeated processing.

---

## Core Features

### 1. Five-Section Research Paper Summarization

ResearchAI converts academic papers into a predictable structure, helping researchers identify essential information without reading the entire document first.

Every generated summary follows five sections:

| Section | Information Provided |
|---|---|
| Title, Authors & Abstract | Paper identity and research overview |
| Problem Statement & Motivation | Research problem and the reason for addressing it |
| Methodology & Architecture | Proposed methods, algorithms, and system design |
| Key Results & Benchmarks | Experimental findings and reported performance |
| Conclusion & Future Directions | Research contributions, limitations, and future work |

The LangGraph workflow uses bounded source context, evidence validation, and controlled output repair. Missing or unsupported information is handled explicitly rather than presented as a verified finding.

### 2. Hybrid Retrieval-Augmented Generation

ResearchAI combines two complementary retrieval techniques.

**Semantic Search — Voyage AI + MongoDB Atlas Vector Search**

Identifies passages based on semantic similarity, allowing the system to retrieve relevant information even when a question uses different wording from the paper.

**Keyword Search — BM25**

Retrieves passages based on exact terms, improving coverage for technical vocabulary, mathematical notation, model names, and specific concepts.

**Reciprocal Rank Fusion (RRF)**

Combines ranked retrieval candidates into a single evidence set for answer generation.

The answer-generation pipeline then uses the selected context to generate responses, validate source references, and abstain when sufficient evidence is unavailable.

This approach is designed to improve evidence coverage compared with relying on semantic similarity alone.

### 3. Interactive PDF Citations

Generated answers and summary sections include source references that can be opened in the original document.

The PDF workspace supports:

- Direct navigation to referenced PDF pages
- Text and source-region highlighting when verified coordinates are available
- Page-level fallback when precise highlighting cannot be established
- Zoom, page navigation, and responsive PDF viewing
- A collapsible evidence section to keep answers readable

The PDF viewer remains closed by default, allowing researchers to focus on reading summaries and conversations. Users open it only when they need to inspect the original evidence.

### 4. Reliable Asynchronous Processing

Research papers may require computationally expensive extraction, embedding, and LLM operations.

ResearchAI uses **RabbitMQ and persistent processing jobs** to handle these operations outside normal HTTP request execution.

The processing system supports retryable jobs, recovery of interrupted work, status tracking, and reuse of completed processing artifacts.

This design separates interactive API requests from longer-running AI workloads and provides a foundation for concurrent document processing.

### 5. Research Dashboard

The React interface provides a centralized document library featuring PDF upload, document search, processing status, sorting, filtering, and paper deletion.

A responsive workspace organizes generated summaries, chatbot conversations, and the optional PDF viewer into a consistent reading experience.

---

## Technology Stack

| Layer | Technologies | Responsibility |
|---|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS | User interface and research workspace |
| Backend | Python, FastAPI, Pydantic | REST APIs, validation, and orchestration |
| Document Parsing | LlamaParse | PDF text, layout, and page-aware extraction |
| Document Chunking | LangChain | Structured text segmentation |
| Embeddings | Voyage AI | Semantic vector generation |
| Database | MongoDB Atlas, GridFS | Document metadata, PDFs, chunks, and vectors |
| Retrieval | Atlas Vector Search, BM25, RRF | Hybrid document retrieval |
| AI Orchestration | LangGraph, LangChain | Summarization and RAG workflows |
| LLM Integration | OpenRouter | Configurable language-model access |
| Background Processing | RabbitMQ | Asynchronous task execution and recovery |
| Evaluation | Ragas, manual source review | Retrieval and generation quality analysis |
| Testing | pytest, Vitest, Playwright | Backend, frontend, and browser verification |
| Deployment | Docker Compose, GitHub Actions | Reproducible development and CI |

---

## Project Structure

```text
Research-Assistant-for-PDFs/
├── frontend/
│   └── src/                    # React interface and PDF workspace
├── backend/
│   ├── gateway/                # FastAPI routes and API contracts
│   ├── services/
│   │   ├── document_processor/ # PDF extraction, chunking, embeddings
│   │   ├── summary_service/    # LangGraph summarization
│   │   ├── rag_service/        # Retrieval and question answering
│   │   └── jobs/               # Background job orchestration
│   ├── shared/                 # Shared models and configuration
│   └── tests/                  # Backend test suite
├── evaluation/                 # Ragas benchmarks and reports
├── docs/                       # Technical and operational documentation
├── docker-compose.yml
├── .env.example
└── README.md
```

Detailed component responsibilities and system data flows are available in [Architecture Documentation](docs/architecture.md).

---

## Getting Started

All commands below are intended to run **from the repository root** unless a step explicitly changes directory. Use **one** application startup method at a time: Docker Compose *or* local development. Running both simultaneously can cause port conflicts.

### Prerequisites

- Git
- **Docker Desktop** with the Docker Compose V2 plugin (for containerized setup)
- **Python 3.11+** (for local backend development; Docker uses Python 3.12)
- **Node.js 22+** and npm (for local frontend development)
- **MongoDB Atlas** database (recommended for full vector and keyword search)
- Working API credentials for **LlamaParse**, **Voyage AI**, and **OpenRouter**

> External AI services may incur charges or require remaining API credits. A successful health check does not verify provider credentials, Atlas search indexes, or AI-generated output.

### Step 1 — Clone the Repository

```bash
git clone https://github.com/arrathikan/Research-Assistant-for-PDFs.git
cd Research-Assistant-for-PDFs
```

If you already cloned the repository, open a terminal in its **root directory** (the folder containing `docker-compose.yml`).

### Step 2 — Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` in an editor and replace placeholders with your own values. At minimum, review:

```dotenv
# Use your real MongoDB Atlas connection string (not localhost in Docker).
MONGODB_URI=your_atlas_connection_string
MONGODB_DB_NAME=research_assistant

LLAMA_CLOUD_API_KEY=YOUR_LLAMA_CLOUD_KEY
VOYAGE_API_KEY=YOUR_VOYAGE_KEY
OPENROUTER_API_KEY=YOUR_OPENROUTER_KEY

# Set this to a model ID actually supported by your OpenRouter account.
PRIMARY_REASONING_MODEL=YOUR_SUPPORTED_OPENROUTER_MODEL_ID

# Application metadata
OPENROUTER_APP_NAME=ResearchAI
OPENROUTER_APP_URL=http://localhost:3000
```

These are **example settings**: keep other values from `.env.example` and replace the placeholders; do not publish actual credentials. The model must be available on your selected provider and within your budget.

If MongoDB credentials include reserved URL characters, URL-encode them.

Configure Atlas Network Access and create the matching vector and keyword indexes before relying on hybrid retrieval.

The default index names are `chunk_embeddings_v1` and `chunk_keywords_v1` (see [MongoDB Atlas Setup](docs/atlas-setup.md)).

**Important database distinction:** The default Compose stack does **not** start a MongoDB server; it uses the URI in `.env`.

The optional Compose `mongodb` service is a separate local-development profile, and standalone local MongoDB does not provide Atlas Vector Search features required by the complete RAG flow.

**Security:** `.env` and `frontend/.env.local` must remain untracked. Never commit API tokens, passwords, connection strings, or provider credentials.

### Option A — Run the Full Application with Docker (Recommended)

Start Docker Desktop first.

From the repository root:

```bash
# Validate Docker Compose configuration
docker compose config -q

# Build images and start all application services
docker compose up -d --build --wait

# Check running services and health status
docker compose ps

# Inspect backend and worker logs
docker compose logs --tail=100 gateway workers
```

#### Application URLs

| Service | Address |
|---|---|
| ResearchAI web application | http://localhost:3000 |
| FastAPI interactive documentation | http://localhost:8000/docs |
| Gateway health endpoint | http://localhost:8000/health |
| RabbitMQ management interface | http://localhost:15672 |

The RabbitMQ management account uses `RABBITMQ_DEFAULT_USER` and `RABBITMQ_DEFAULT_PASS` from `.env`.

The example defaults are `guest` / `guest` for local development only.

#### Verify Backend Health

```bash
curl -f http://localhost:8000/health
```

#### View Application Logs

```bash
# Backend logs
docker compose logs -f gateway

# Background worker logs
docker compose logs -f workers

# RabbitMQ logs
docker compose logs -f rabbitmq
```

Press `Ctrl+C` to stop following logs.

#### Stop the Application

```bash
docker compose down
```

This removes the running Compose containers and network but preserves named volumes.

#### Restart the Application

```bash
docker compose up -d --wait
```

#### Rebuild After Code Changes

```bash
docker compose up -d --build --wait
```

#### Optional Local MongoDB

To run the optional local MongoDB service:

```bash
MONGODB_URI=mongodb://mongodb:27017 docker compose --profile local up -d --build --wait
```

**Note:** The local MongoDB setup is intended for infrastructure testing. It is not a substitute for MongoDB Atlas when testing Atlas Vector Search and the full hybrid RAG workflow.

See the [Deployment Guide](docs/deployment.md) for additional configuration.

---

### Option B — Run Locally for Development (macOS / Linux)

Use this option when developing or debugging the backend and frontend without containerizing the entire application.

Keep **MongoDB Atlas** configured in the root `.env`.

Start each process in a separate terminal.

Do not run the full Docker Compose application simultaneously because both configurations may use the same ports.

#### Terminal 1 — Start RabbitMQ

From the repository root:

```bash
docker compose up -d rabbitmq
```

The example configuration uses:

```dotenv
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

If you changed the RabbitMQ credentials, update the connection URL accordingly.

#### Terminal 2 — Start FastAPI Backend

From the repository root:

```bash
# Create Python virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install backend dependencies
python -m pip install -r backend/requirements.txt

# Start FastAPI development server
python -m uvicorn backend.gateway.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend is available at:

- API: http://localhost:8000
- Swagger documentation: http://localhost:8000/docs
- Health endpoint: http://localhost:8000/health

#### Terminal 3 — Start Background Worker

Open another terminal in the repository root:

```bash
# Activate existing virtual environment
source .venv/bin/activate

# Start document-processing worker
python -m backend.services.jobs.main run
```

The worker processes background jobs, including document extraction, embedding generation, and summarization.

#### Terminal 4 — Start React Frontend

Open another terminal in the repository root:

```bash
# Enter frontend directory
cd frontend

# Configure local API URL
printf 'VITE_API_BASE_URL=http://localhost:8000/api/v1\n' > .env.local

# Install exact dependencies from package-lock.json
npm ci

# Start Vite development server
npm run dev
```

Open:

**http://localhost:5173**

The frontend communicates with the FastAPI backend at `http://localhost:8000/api/v1`.

The root `.env` is used for backend configuration, while `frontend/.env.local` configures the local frontend.

**Security:** Never expose provider API keys in variables beginning with `VITE_`, because these values become visible in the browser bundle.

#### Stop Local Development

Press `Ctrl+C` in the FastAPI, worker, and frontend terminals.

Then, from the repository root:

```bash
docker compose stop rabbitmq
```

---

### Troubleshooting

| Problem | Recommended Solution |
|---|---|
| `backend/requirements.txt` not found | Run the command from the repository root, not the `frontend/` directory. |
| Port 8000 is already in use | Stop the existing backend process before starting another one. |
| Port 3000 or 5173 is already in use | Stop the conflicting frontend process. |
| Docker backend cannot connect to MongoDB | Verify the Atlas URI, credentials, and Network Access settings. |
| Worker is unhealthy | Inspect worker and RabbitMQ logs. |
| PDF processing remains pending | Check RabbitMQ, worker connectivity, provider credentials, and processing errors. |
| API health works but RAG fails | Verify Atlas search indexes, embedding configuration, API keys, and provider credits. |
| Frontend cannot connect to the backend | Check the frontend API URL and confirm FastAPI is running. |
| Docker Compose fails to start | Run `docker compose config -q`, `docker compose ps`, and inspect logs. |

Useful troubleshooting commands:

```bash
# View running containers
docker compose ps

# View recent logs
docker compose logs --tail=100

# View gateway logs
docker compose logs --tail=100 gateway

# View worker logs
docker compose logs --tail=100 workers

# Check FastAPI health
curl http://localhost:8000/health
```

---

## API Overview

ResearchAI provides document-oriented REST endpoints.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/documents` | Upload a PDF |
| GET | `/api/v1/documents/{id}/summary` | Retrieve saved structured summary |
| GET | `/api/v1/documents/{id}/chunks` | Retrieve processed chunks |
| POST | `/api/v1/documents/{id}/chat` | Ask a question about a paper |
| GET | `/api/v1/documents/{id}/chat/{conversation_id}` | Retrieve conversation history |
| DELETE | `/api/v1/documents/{id}` | Delete a paper and associated data |

Refer to [Gateway Documentation](backend/gateway/README.md) for complete request contracts, status handling, and additional routes.

---

## RAG Evaluation and Quality Assurance

ResearchAI includes an offline evaluation workflow built with **Ragas** and curated source-grounded questions.

The evaluation process separates retrieval performance from answer-generation quality.

| Metric | Evaluation Objective |
|---|---|
| Context Precision | Relevance of retrieved supporting passages |
| Context Recall | Coverage of information required to answer |
| Faithfulness | Consistency of generated claims with retrieved evidence |
| Answer Relevancy | Relevance of generated responses to questions |
| Factual Correctness | Agreement with reference answers |

The benchmark includes answerable and unanswerable questions and supports comparisons between semantic-only and hybrid retrieval strategies.

### Evaluation Approach

1. Collect and validate research questions and supporting references.
2. Execute the RAG pipeline against a controlled benchmark.
3. Calculate applicable Ragas metrics.
4. Review answer quality and citation support.
5. Record unsupported claims, incorrect responses, false abstentions, and other failure cases.

Evaluation executes separately from normal chat requests to avoid unnecessary cost and latency.

**Evaluation transparency:** Benchmark reports document observed answer-quality limitations, incomplete citation support, and metric execution errors.

Successful integration tests do not imply that scientific-answer accuracy has been fully established.

See [Evaluation Methodology](evaluation/README.md) and [Latest QA Evaluation Report](evaluation/reports/2026-11-13-final-qa/README.md).

---

## Testing and Verification

The project uses multiple testing levels to check component behavior and integration.

### Backend Testing

From the repository root, with the Python virtual environment activated:

```bash
PYTHONPATH=. python -m pytest backend/tests/ -q
```

### Frontend Testing

From the repository root:

```bash
cd frontend

# Install dependencies
npm ci

# TypeScript checks
npm run typecheck

# Unit tests
npm run test

# Production build verification
npm run build
```

### Browser Testing

From the repository root:

```bash
cd frontend

# Install required Playwright browsers
npx playwright install

# Run end-to-end tests
npm run test:e2e
```

Browser tests may require the application or test server to be running, depending on the Playwright configuration.

Testing covers document validation, storage behavior, retrieval contracts, source citation handling, background processing, frontend interactions, and responsive navigation.

GitHub Actions automates selected backend, frontend, and Docker smoke checks without requiring paid AI provider execution during standard CI runs.

The [Final QA Report](docs/final-qa.md) documents test coverage, live integration checks, and outstanding limitations.

---

## Engineering Decisions

| Decision | Rationale |
|---|---|
| Hybrid RAG instead of semantic-only retrieval | Improve coverage of both conceptual and exact technical queries |
| MongoDB GridFS | Store original PDF files alongside document metadata |
| MongoDB Atlas Vector Search | Integrate semantic retrieval with existing document storage |
| LangGraph for summarization | Coordinate stateful processing and controlled validation |
| RabbitMQ background workers | Separate long-running AI operations from HTTP requests |
| Versioned processing artifacts | Support reproducibility and reuse of completed work |
| Document-scoped retrieval | Restrict retrieved evidence to the selected research paper |
| Source citation validation | Reduce unsupported source references |
| Offline Ragas evaluation | Measure retrieval and generation quality without increasing normal chat latency |

These decisions prioritize maintainability, traceability, reliability, and the ability to evaluate system behavior.

---

## Current Limitations

ResearchAI is an actively developed engineering project.

Its architecture and workflows have been exercised through automated tests and selected live provider integrations, but additional validation is required before public production deployment.

Current areas for improvement include:

- Strengthening the completeness and factual consistency of generated summaries
- Improving citation support and reducing unsupported research answers
- Expanding benchmarks across different document formats and research domains
- Completing provider-specific compatibility and live end-to-end checks
- Addressing remaining deployment hardening and dependency advisories

Provider limitations, unsupported document content, and model failures may prevent successful summary generation.

The system does not guarantee that every answer or citation is correct; users should verify important research claims against the original paper.

See [Latest Live QA](docs/live-e2e-qa-2026-11-14.md) for verified results and outstanding issues.

---

## Future Improvements

Planned enhancements include:

- Broader research-paper evaluation datasets and automated regression benchmarks
- Improved retrieval reranking and evidence selection
- Stronger summary validation and recovery strategies
- Expanded multi-document research and cross-paper comparison
- Authentication, access-control hardening, and production observability

---

## Documentation

- [System Architecture](docs/architecture.md)
- [Deployment and Configuration](docs/deployment.md)
- [MongoDB Atlas Setup](docs/atlas-setup.md)
- [Hybrid RAG Implementation](docs/hybrid-rag.md)
- [Structured Summarization](docs/structured-summary.md)
- [PDF Citation System](docs/pdf-citations.md)
- [Background Processing](docs/background-jobs.md)
- [Ragas Evaluation](evaluation/README.md)
- [Interview Demo Guide](docs/demo-guide.md)
- [Final Quality Assurance](docs/final-qa.md)

---

## Author

**Aravinthan Arrathikasarma**

AI Undergraduate — University of Moratuwa, Sri Lanka

- GitHub: [@arrathikan](https://github.com/arrathikan)
- LinkedIn: [Aravinthan Arrathikasarma](https://www.linkedin.com/in/aravinthan-arrathikasarma/)

---

**ResearchAI — Turning complex research papers into structured knowledge with verifiable AI assistance.**
