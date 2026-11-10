# RAG Service (`backend/services/rag_service/`)

Core conversational retrieval-augmented generation engine powering academic question answering.

---

## Retrieval Architecture

1. **Semantic Vector Search:** Dense representations computed via Voyage AI (`voyage-3`).
2. **Lexical Keyword Search:** BM25 scoring targeting exact terminology, notation, and author names.
3. **Reciprocal Rank Fusion (RRF):** Interleaves rankings from sparse and dense retrievers to produce a unified context candidate list.
4. **Citation Extraction:** Associates each factual statement in the answer with an explicit PDF page number and snippet reference.

---

## Running Locally

```bash
python -m backend.services.rag_service.main
```
