# Atlas live verification — 2026-11-11

## Confirmed results

- Atlas authentication and application database access succeeded after the current
  client IP was added to the project's access list.
- The separately enabled `test_live_atlas_hybrid_chat_document_isolation` passed
  with real Voyage embeddings, Atlas Vector Search, MongoDB Search BM25, Python
  RRF and OpenRouter generation. The answer included a verified citation and the
  score stated in the synthetic input; its sources belonged to the chosen document.
- Both configured application search indexes are compatible and queryable.
- The local gateway was restarted with current code, dependencies and Atlas
  settings. Health returned 200, chat/summary routes appeared in OpenAPI, and a
  database-backed unknown-document lookup returned the expected 404.
- Full backend regression against disposable local MongoDB: **303 passed, 4
  optional live tests skipped**. The real Atlas check ran separately: **1 passed**.
- Scoped Ruff lint/format checks and the new database-name regression test passed.

## Failure and correction

The first live check failed because its generated database name exceeded this
cluster's 38-byte maximum. The generic storage error also obscured that failed
cleanup used the same invalid name. Redacted command diagnostics identified Atlas
error code 8000 and the database-name limit. The corrected helper uses a short,
uniquely generated researchai_test namespace. This change affects live test names,
not application data or production database naming.

## Scope and limits

The test used synthetic parsed artifacts and synthetic PDF bytes. LlamaParse was
not called as part of this Atlas check; its real parsing smoke test was verified
separately earlier. No private research PDF, real conversation, credential or raw
retrieval result was committed. Only the test's freshly generated database was
removed. Application indexes were created without replacing existing definitions.

Existing local-preview database files remain on disk and were not migrated to
Atlas. The gateway now reads Atlas through the ignored local environment. New
uploads need parsing/chunking/embedding before retrieval; automatic background
orchestration is a later stage. This smoke test does not establish RAG accuracy,
Ragas scores, scientific correctness or the superiority of hybrid retrieval.
