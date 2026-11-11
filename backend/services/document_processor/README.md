# Document Processor Service (`backend/services/document_processor/`)

Asynchronous background worker responsible for parsing academic PDFs into structured Markdown and dividing them into search-optimized chunks.

---

## Responsibilities

1. **Queue Consumer:** Listens to `document_ingestion_queue` on RabbitMQ.
2. **LlamaParse Integration:** Extracts clean Markdown from PDF binaries while preserving page breaks (`--- Page X ---`).
3. **Markdown-Aware Chunking:** Utilizes LangChain `MarkdownHeaderTextSplitter` and `RecursiveCharacterTextSplitter` to segment content logically.
4. **Metadata Preservation:** Injects page numbers, section titles, and document IDs into each chunk payload before forwarding to the embedding pipeline.

---

## Running Locally

```bash
python -m backend.services.document_processor.main
```

## Supported LlamaParse adapter (Prompt 6.2)

New extraction uses the provider's unified `llama-cloud` SDK (tested with 2.19.0)
and LlamaParse v2. The deprecated `llama-parse` package is replaced in dependency
files; no legacy parsing API is called. PDF bytes are sent directly with a generic
`source.pdf` name, and structured output expands Markdown, items and metadata.
SDK calls disable automatic retries to avoid accidentally submitting repeated
paid jobs. Cloud request/polling failures return safe generic errors.

Settings: `LLAMA_CLOUD_API_KEY`, positive `LLAMA_PARSE_TIMEOUT_SECONDS` (300),
`LLAMA_PARSE_TIER` (agentic), and `LLAMA_PARSE_VERSION` (latest). Choose a supported
fixed provider version for reproducible extraction. Using latest can change output
over time. Calls may consume credits. No live call is made by deterministic tests.

Page-point bounding boxes, including multiple boxes and nested item relationships,
are preserved. Missing boxes remain absent; table rows/HTML/CSV and heading levels
are retained when returned. Provider page failures stop extraction instead of
silently accepting partial content.

References: [v2 Python quickstart](https://developers.llamaindex.ai/llamaparse/parse/getting_started/)
and [response format](https://developers.llamaindex.ai/llamaparse/parse/guides/response-format/).

## Persistence and recovery

`parse_pdf(database, document_id, settings)` loads and validates the GridFS PDF,
claims parsing atomically, calls LlamaParse and saves the result. Per-run page and
source records are published only by a conditional active-run pointer update.
`read_parsed_document` returns only that complete run. New indexes support run
and page lookups. Completed extraction is reused; FAILED documents can be retried.

A missing key leaves the document unchanged. Provider, validation or persistence
failures set a safe FAILED status. If the database is unavailable, failure status
may itself be impossible to save. A process crash leaves a RUNNING claim: inspect
the provider job and database before manually recovering it. Partially written
runs remain unreferenced for operator reconciliation; no destructive automatic
cleanup or automatic paid retry is performed.
