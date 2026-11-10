# Evaluation Subsystem (`evaluation/`)

The evaluation subsystem provides offline benchmarking tools and datasets for measuring the quality, faithfulness, and retrieval performance of the ResearchAI RAG pipeline.

---

## Evaluation Guidelines (AGENTS.md Compliance)

1. **Framework:** Powered by Ragas (modern collections-based `EvaluationDataset` and `evaluate()` API) with manual verification.
2. **Decoupled Architecture:** Runs completely offline, separated from live user chat sessions.
3. **Core Metrics:**
   - **Retrieval:** *Context Precision* (relevance ordering), *Context Recall* (coverage of ground truth).
   - **Generation:** *Faithfulness* (groundedness in context), *Answer Relevancy* (responsiveness to query), *Factual Correctness*.
4. **Benchmark Dataset (`benchmark_dataset.json`):** Curated set containing both **answerable questions** and **unanswerable questions** to validate model abstention and hallucination guardrails.
5. **Comparative Analysis:** Compares Hybrid Retrieval (Vector + BM25 + RRF) against semantic-only retrieval.

---

## Directory Structure

```
evaluation/
├── README.md               # Guidelines and usage instructions
├── schemas.py              # Pydantic validation models for evaluation samples
├── benchmark_dataset.json  # Curated benchmark queries with ground truth
└── reports/                # Versioned evaluation results and benchmark scores
    └── README.md
```
