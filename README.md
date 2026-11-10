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
