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
successful validation. MongoDB publication and React integration follow next.
