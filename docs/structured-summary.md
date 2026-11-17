# Structured research summaries

The five sections are Title, Authors and Abstract; Problem Statement; Methodology;
Key Results; Conclusion. The internal draft schema requires current source quotes
for populated fields. Missing facts are null/empty and appear as “Not stated in
the document.” No example paper content is substituted for a real summary.

## Generation and validation

`backend/services/summary_service/workflow.py` builds a deterministic LangGraph:
identify → generate → validate → advance/combine → save, with bounded conditional
repair. All page-attributed chunks enter heading-labeled windows; long papers
reduce validated notes through a bounded tree. Sources are checked again at every
level. A preflight rejects oversized input before a paid request; text is not
silently truncated. Reduction must make progress and has at most eight rounds.

OpenRouter receives a strict JSON schema and parameter-compatible provider routing.
There is no hidden model fallback. Transport retries cover transient network,
408/429 and selected 5xx errors; invalid model/auth/credit errors stop safely.
Truncated/incomplete output is rejected. Model reasoning shares the output budget;
see [provider settings](provider-configuration.md).

| Setting | Default | Meaning |
| --- | --- | --- |
| `LLM_TIMEOUT_SECONDS` | 60 | Timeout per completion request |
| `LLM_MAX_OUTPUT_TOKENS` | 4096 | Output budget including reasoning |
| `SUMMARY_CONTEXT_BYTES` | 48000 | UTF-8 context guard, not tokens |
| `SUMMARY_MAX_WINDOWS` | 64 | Extraction-window bound |
| `SUMMARY_VALIDATION_RETRIES` | 2 | Targeted repairs per invalid output |

Validation requires source identity, correct page and an exact contiguous quote
with whitespace normalization. It does not establish that a claim follows from
that quote. Runtime prompt guidance and repair feedback preserve strict validation;
full-paper generations can still fail. Inspect claims against original pages.

## Execution and publication

The worker supervisor runs ingestion followed by the summary consumer:

```bash
python -m backend.services.jobs.main run
```

For explicit operator processing of an already parsed/chunked document:

```bash
python -m backend.services.summary_service.main DOCUMENT_ID
curl http://localhost:8000/api/v1/documents/DOCUMENT_ID/summary
```

Avoid concurrent manual processing of active jobs. Generation consumes credits;
GET only reads. Repeating a compatible completed result reuses it. Failed terminal
jobs can use the documented processing retry endpoint; valid parse/chunk/embedding
outputs are reused, although failed summary extraction may repeat paid calls.

Immutable `summary_runs` are identified by document, active chunk set and profile
(model, schema, workflow, limits and relevant reasoning policy). Ownership and
unchanged source-generation checks guard publication. A saved run left by a pointer
publication failure can be recovered on retry. Reads reject stale references.

The API returns 404 for an unknown paper, 409 for unavailable/stale/in-progress
output and 503 for failed generation or invalid/unavailable storage. Summary
completion marks a document READY only when current configured embeddings are
also complete. Atlas search-index readiness is a separate check. Interrupted work
requires [reviewed recovery](background-jobs.md), not a fabricated READY state.

## Frontend and verification

The summary panel shows saved sections and clickable verified citations. Loading,
processing and failure states are explicit; retrying a read never starts a paid
job. Late responses for a different selected document are discarded. Opening or
closing the PDF retains summary/chat state.

[CI](ci.md) documents deterministic workflow/source tests and opt-in provider
markers. Historical [final QA](final-qa.md) records a successful repaired public
summary; [later live QA](live-e2e-qa-2026-11-14.md) records further strict-quote
failures. These observations do not establish summary accuracy across papers or
models. Current cleanup checks are in [the submission review](submission-review.md).
