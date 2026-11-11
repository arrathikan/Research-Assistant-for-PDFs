# Hybrid RAG service

Document-scoped Voyage query embeddings + Atlas Vector Search + MongoDB Search
BM25 + Python RRF, followed by an ordinary LangChain answer/citation chain.

```bash
python -m backend.services.rag_service.indexes
python -m backend.services.rag_service.indexes --create
python -m backend.services.rag_service.main DOCUMENT_ID "What method is described?"
```

Both Atlas indexes must be queryable; ordinary local MongoDB is insufficient.
The API exposes POST `/api/v1/documents/{id}/chat` and GET
`/api/v1/documents/{id}/chat/{conversation_id}`. Internal evaluation traces are
available through `chat_with_trace`; public responses/history exclude them.
See [the RAG guide](../../../docs/hybrid-rag.md) for setup, tests and limitations.
