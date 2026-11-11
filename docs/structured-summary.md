# Structured research summaries (Prompt 9)

The summary format is Title/Authors/Abstract, Problem Statement, Methodology,
Key Results and Conclusion. The internal `SummaryDraft` schema requires explicit
source quotes for populated fields. Missing information is represented as null
(or an empty author list), then displayed as "Not stated in the document."

The OpenRouter client calls only `https://openrouter.ai/api/v1/chat/completions`.
It uses the configured primary model, application attribution, a strict JSON
schema and provider routing that requires the requested parameters. It does not
follow redirects or automatically change models. GPT-5 models use low reasoning
effort and omit temperature; other models use `LLM_TEMPERATURE`.

Transport retries (`LLM_MAX_RETRIES`, 0–5) cover timeouts, connection failures,
408, 429 and selected 5xx responses. Authentication, credit, invalid request and
unsupported-model errors stop immediately with safe messages. Incomplete/truncated
outputs are rejected. Raw provider responses and private paper text are not logged.

Additional settings in `.env.example`:

| Setting | Default | Meaning |
| --- | --- | --- |
| `LLM_TIMEOUT_SECONDS` | 60 | Timeout for a completion request |
| `LLM_MAX_OUTPUT_TOKENS` | 4096 | Completion budget, including model reasoning |
| `SUMMARY_CONTEXT_BYTES` | 48000 | UTF-8 guard for one source/notes context; not tokens |
| `SUMMARY_MAX_WINDOWS` | 64 | Maximum extraction windows before rejecting oversized input |
| `SUMMARY_VALIDATION_RETRIES` | 2 | Maximum targeted repairs per model output |

Evidence validation checks that each cited chunk is in the supplied input, that
its page is correct, and that the quote exists in that page's chunk span (allowing
whitespace normalization). This establishes source identity and quote presence;
it does not prove that a generated claim follows from the quote. Manually review
scientific claims and use the later evaluation stage for quality measurement.

## LangGraph workflow

`identify -> generate -> validate -> advance -> save`, with conditional edges
back to `generate` for at most two targeted repairs. Long papers run extraction
over all page-attributed chunks in bounded, heading-labelled windows, then combine
validated notes through a reduction tree. Original source references are retained
and checked at every level. No input text is silently truncated. A preflight
checks all window/record limits before the first paid request. Reduction must
make progress and is capped at eight rounds.

The graph has no agents, tools, persistent checkpoints or hidden model fallback.
Transport failures do not consume the schema-repair budget; each transport request
has its own bounded retry budget. Failed jobs currently restart extraction on
retry, so they may repeat successful paid calls. Save callbacks run only after
successful validation. MongoDB publication is implemented below; React integration follows next.

## Generate and retrieve

Run from the project root with the backend dependencies installed and MongoDB
running. Use the real document ID returned by upload:

```bash
python -m backend.services.document_processor.main DOCUMENT_ID
python -m backend.services.document_processor.chunk_cli DOCUMENT_ID
python -m backend.services.summary_service.main DOCUMENT_ID
curl http://localhost:8000/api/v1/documents/DOCUMENT_ID/summary
```

The parsing and summary commands can consume credits. Repeating an unchanged
completed summary reuses the stored result. A missing model key does not prevent
reading/reusing an existing valid summary. Generation is explicit until RabbitMQ
orchestration is implemented; the GET endpoint never starts processing.

`summary_runs` holds immutable results keyed by document, active chunk set and
summary profile (model, schema, workflow and relevant limits). The document stores
an active-summary pointer, parse/chunk generation, summary status and ownership
token. Only the owning job can publish against an unchanged source generation.
A saved result left by a publication failure can be reused on retry. Older results
remain stored; switching models/configuration requires a matching result. Reads
revalidate references against current chunk/page text and refuse stale results.

The endpoint returns 404 for an unknown document, 409 for a missing/stale/in-progress
summary and 503 for failed generation or unavailable/invalid storage. Responses
include the five sections, verified source quotes, unavailable field names, model,
profile and chunk-set identifiers.

A completed summary sets the document to READY only when current configured
embeddings for those chunks are also complete; otherwise it remains PENDING.
Atlas index availability is a separate readiness check and is not established by
summary completion. Failed jobs retain a safe failure status. A process crash may
leave a RUNNING claim: inspect that job before manually recovering ownership;
there is no automatic stale-claim takeover in this stage.
