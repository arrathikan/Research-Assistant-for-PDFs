# ResearchAI — AI Research Paper Assistant

ResearchAI is an intelligent, full-stack research assistant designed for reading, analyzing, and synthesizing academic PDFs. It combines automated structured summarization with a hybrid retrieval-augmented generation (RAG) chatbot and an interactive PDF viewer featuring jump-to-source citation highlighting.

---

## 📑 Core Features

1. **Academic PDF Upload & Deduplication:**
   - Single-paper upload with strict MIME and size validation.
   - SHA-256 content hashing to detect duplicates instantly and prevent redundant processing.
   - Persistent raw PDF binary storage in MongoDB GridFS.

2. **Automated 5-Part Structured Summary (LangGraph):**
   - Deterministic multi-stage state graph extracting:
     - **Title, Authors & Abstract**
     - **Problem Statement**
     - **Methodology**
     - **Key Results**
     - **Conclusion**

3. **Conversational Hybrid RAG Chatbot:**
   - **Semantic Search:** Voyage AI state-of-the-art dense embeddings (`voyage-3`).
   - **Lexical Search:** BM25 keyword matching for exact technical formulas, symbols, and author references.
   - **Reciprocal Rank Fusion (RRF):** Fuses sparse and dense rankings for superior context retrieval.
   - Guardrailed responses preventing hallucination on questions out of paper scope.

4. **Interactive PDF Viewer & Source Citation Highlighting:**
   - Embedded PDF viewer powered by React-PDF / PDF.js.
   - Clickable citations in the chat stream (e.g., `[Page 4, Section 3.2]`) automatically scroll to the exact page and highlight the supporting evidence.

---

## 🛠️ Technology Stack

| Domain | Technology | Purpose |
|---|---|---|
| **Frontend** | React, TypeScript, Vite, Tailwind CSS | Responsive split-view workspace |
| **PDF Viewer** | React-PDF / PDF.js | Canvas rendering, text layer & citation highlighting |
| **Backend API** | Python 3.11+, FastAPI, Pydantic v2 | High-performance REST endpoints |
| **Job Queue** | RabbitMQ | Asynchronous PDF ingestion & summarization worker |
| **PDF Extraction** | LlamaParse | Academic layout parsing to clean Markdown |
| **Chunking** | LangChain Markdown-aware splitters | Structure- and page-preserving chunking |
| **Embeddings** | Voyage AI | Domain-optimized dense vector representations |
| **Database** | MongoDB Atlas + GridFS | Metadata, summary storage, raw PDF binaries, vector index |
| **Hybrid Search**| Dense Vector + BM25 + RRF | High-recall academic retrieval |
| **Summarizer** | LangGraph | Deterministic multi-step academic summarizer |
| **Chat Engine** | LangChain + Configurable LLM | Conversational QA with source references |
| **Evaluation** | Ragas | Faithfulness, context recall, and answer relevance |
| **Testing** | pytest + Vitest | Unit, integration, and UI testing |
| **DevOps** | Docker Compose + GitHub Actions | Containerization & automated CI pipelines |

---

## 📁 Repository Structure

```
.
├── AGENTS.md                   # Engineering standards, mentor persona & Git rules
├── README.md                   # Project documentation & overview
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── docs/                       # Architectural & development documentation
│   ├── architecture.md         # Detailed system design & data flow diagrams
│   └── development-roadmap.md  # Multi-stage roadmap & increment tracker
├── backend/                    # FastAPI services & worker (Stage 1+)
└── frontend/                   # React + Vite application (Stage 1+)
```

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- Docker & Docker Compose
- Node.js 18+ & npm
- Python 3.11+
- API Keys: [LlamaParse](https://cloud.llamaindex.ai/), [Voyage AI](https://www.voyageai.com/), and an LLM provider (OpenAI, Anthropic, or Google)

### 2. Environment Setup
Copy the environment template and populate your API credentials:
```bash
cp .env.example .env
```

### 3. Start Infrastructure
Start the RabbitMQ and MongoDB instances via Docker Compose:
```bash
docker-compose up -d
```

---

## 📖 Documentation & Guidelines

- **[AGENTS.md](AGENTS.md):** Complete project rules, Conventional Commit standards, and 20 automatic Git rules.
- **[docs/architecture.md](docs/architecture.md):** Architectural diagrams, data flows, MongoDB schemas, and RAG retrieval pipelines.
- **[docs/development-roadmap.md](docs/development-roadmap.md):** Stage-by-stage implementation tracker.
