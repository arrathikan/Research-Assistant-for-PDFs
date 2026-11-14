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

### Prerequisites

- Python 3.11+
- Node.js 22+
- Docker Desktop with Docker Compose
- MongoDB Atlas connection
- API credentials for the configured LlamaParse, Voyage AI, and OpenRouter providers

External providers may require a paid account or available usage credits.

### 1. Clone the Repository

```bash
git clone https://github.com/arrathikan/Research-Assistant-for-PDFs.git
cd Research-Assistant-for-PDFs
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Update `.env` with the MongoDB connection string and the API credentials required by your selected providers.

Refer to [Provider Configuration](docs/provider-configuration.md) for supported settings and model compatibility.

**Security:** Never commit `.env`, API keys, database passwords, or provider credentials to version control.

### 3. Run with Docker

```bash
docker compose up -d --build --wait
```

Open the application at:

**http://localhost:3000**

Docker Compose starts the configured application components, including the frontend, API gateway, RabbitMQ, and processing workers.

For deployment configuration and troubleshooting, see [Deployment Guide](docs/deployment.md).

### Alternative: Local Development

Start RabbitMQ:

```bash
docker compose up -d rabbitmq
```

Install backend dependencies and start the gateway:

```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.gateway.main:app --host 127.0.0.1 --port 8000 --reload
```

Run the background worker in a separate terminal:

```bash
python -m backend.services.jobs.main run
```

Start the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

The native development setup uses the configured MongoDB Atlas deployment.

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

**Evaluation transparency:** Benchmark reports document observed answer-quality limitations, incomplete citation support, and metric execution errors. Successful integration tests do not imply that scientific-answer accuracy has been fully established.

See [Evaluation Methodology](evaluation/README.md) and [Latest QA Evaluation Report](evaluation/reports/2026-11-13-final-qa/README.md).

---

## Testing and Verification

The project uses multiple testing levels to check component behavior and integration.

**Backend testing**

```bash
PYTHONPATH=. python -m pytest backend/tests/ -q
```

**Frontend testing**

```bash
cd frontend
npm run typecheck
npm run test
npm run build
```

**Browser testing**

```bash
cd frontend
npm run test:e2e
```

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

ResearchAI is an actively developed engineering project. Its architecture and workflows have been exercised through automated tests and selected live provider integrations, but additional validation is required before public production deployment.

Current areas for improvement include:

- Strengthening the completeness and factual consistency of generated summaries
- Improving citation support and reducing unsupported research answers
- Expanding benchmarks across different document formats and research domains
- Completing provider-specific compatibility and live end-to-end checks
- Addressing remaining deployment hardening and dependency advisories

Provider limitations, unsupported document content, and model failures may prevent successful summary generation. The system does not guarantee that every answer or citation is correct; users should verify important research claims against the original paper.

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
