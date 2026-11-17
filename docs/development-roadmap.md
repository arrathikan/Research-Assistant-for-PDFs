# Implementation status and remaining work

This page describes the current code, rather than the development prompts used
to build it. Verification is recorded separately in [the submission review](submission-review.md).

## Implemented

| Capability | Implementation |
| --- | --- |
| HTTP gateway | Validated upload, status, original PDF, summary, chat, citation and deletion routes |
| Persistence | MongoDB metadata, SHA-256 deduplication and GridFS originals |
| Parsing/chunking | LlamaParse v2; page/heading-aware LangChain character chunking |
| Embeddings/search | Voyage profiles/cache; Atlas vector + BM25 + RRF |
| Summaries | Five-section LangGraph workflow with bounded repair and source validation |
| Research chat | Document-scoped answers, metadata context, follow-ups, labeled general background |
| Source inspection | Optional React-PDF viewer, verified citations, supported highlighting/page fallback |
| Background processing | MongoDB outbox, RabbitMQ workers, idempotent claims and bounded recovery |
| Frontend | Orange ResearchAI library, upload dialog, status cards, summary and chat workspace |
| Evaluation | Optional offline Ragas runner, curated public datasets, explicit failure/review reports |
| Delivery checks | Docker/Nginx, GitHub Actions, unit/integration and Chromium browser suites |

Implementation is not a claim that every live model response passes validation
or that every paper yields a scientifically complete summary.

## Before a dependable interview demonstration

- Run a successful complete paper upload/summary/chat workflow with the chosen
  funded model; preserve a clearly labeled previously verified result as fallback.
- Review returned claims and citations against original pages. Full-paper strict
  quote failures and previous attribution/coverage problems remain documented.
- Remediate dependency advisories with a separately tested upgrade; do not publish
  a security-ready claim based on unit tests or CORS.
- Independently review benchmark references and complete missing/error metrics
  before presenting general accuracy or hybrid-versus-semantic conclusions.
- Retest the rapid-tab-switch/instant-refresh navigation edge case from live QA.

## Broader limitations

Authentication, authorization, public TLS operations, account-based cross-device
libraries, arbitrary metadata search, vision completion, automatic LLM fallback
and Voyage reranking are not implemented. Ordinary local MongoDB is not an Atlas
search substitute. Process liveness is separate from provider/index readiness.

Historical QA and design records are retained in [the documentation index](README.md)
so measured failures, contribution history and earlier verification remain visible.
