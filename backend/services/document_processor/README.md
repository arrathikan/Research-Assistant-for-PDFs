# Document extraction service

Prompt 6 parses an uploaded PDF into page-aware Markdown using LlamaParse v2.
Prompt 7 adds local Markdown chunking. Embeddings, summaries and RabbitMQ
dispatch remain later stages. Uploads do not start paid extraction automatically.

## Setup and execution

Install the backend requirements in a Python 3.11+ environment. The tested
provider package is `llama-cloud` 2.19.0, the supported unified SDK for LlamaParse.
The deprecated `llama-parse` package is replaced; this service uses no v1 API.

Configure these variables in the root `.env` or process environment:

| Variable | Default / purpose |
| --- | --- |
| `MONGODB_URI` | Atlas or local database containing the uploaded PDF |
| `MONGODB_DB_NAME` | `research_assistant` |
| `LLAMA_CLOUD_API_KEY` | Required; never commit it |
| `LLAMA_PARSE_TIMEOUT_SECONDS` | `300`, positive request/polling bound |
| `LLAMA_PARSE_TIER` | `agentic`; also fast, cost_effective, agentic_plus |
| `LLAMA_PARSE_VERSION` | `latest`; choose a supported fixed version for reproducibility |

From the repository root, using the real document ID returned by upload:

```bash
python -m backend.services.document_processor.main DOCUMENT_ID
curl http://localhost:8000/api/v1/documents/DOCUMENT_ID
curl http://localhost:8000/api/v1/documents/DOCUMENT_ID/parsed
```

The CLI validates the identifier/key, retrieves original GridFS bytes, validates
the PDF again, claims parsing and calls LlamaParse. PDF bytes use a generic
`source.pdf` upload name; no extracted paper or temporary PDF is written into
the repository. Calls may consume provider credits and transmit that PDF to
LlamaParse. SDK automatic retries are disabled to avoid repeated paid submissions.
The CLI logs completion metadata or safe errors, never extracted paper text.

`GET /api/v1/documents/{id}/parsed` returns published pages and source elements.
It is read-only and never invokes the provider. Unfinished extraction returns
409, unknown documents 404, malformed IDs 422 and storage failures 503.
For internal chunking, `read_parsed_document(...).as_markdown()` includes explicit
`--- Page N ---` separators.

## Source attribution

Page numbers are explicit and one-based. The parser must return all original
pages exactly once. Failed pages, empty extraction and ambiguous numbering are
rejected; blank pages remain represented when other pages contain text.
Markdown preserves headings, paragraphs and tables. Source elements retain
text/Markdown, IDs, page number, nesting and available table/heading metadata.

Current v2 item boxes are in page points. All boxes and page dimensions are
preserved; optional missing/invalid boxes remain absent. Unknown provider units
remain marked as provider-defined rather than being guessed. Page navigation
is the fallback; exact PDF highlighting is not implemented by this stage.

## Lifecycle and persistence

`parse_pdf(database, document_id, settings)` atomically claims a pending/failed
document; concurrent running or completed claims cannot start another paid call.
Completed results are reused. Status during work is `PARSING`, with
`parsing_status=RUNNING`. On success, parsing_status becomes `COMPLETED`, parsed_at
is saved, and overall status returns to `PENDING` for the next stage. The document
is not READY for chat until later processing completes.

Each attempt writes immutable `parsed_pages` and `source_elements` records with
a parse_run_id. Run/page indexes support retrieval. An ownership-checked metadata
update publishes active_parse_run_id only after every write succeeds. Readers
filter by that pointer, so partial runs cannot appear as complete results.
The SDK version, configured provider version/tier and provider job ID are stored.
Using latest can change output over time.

A missing key leaves the document unchanged. Provider/validation/persistence
failures set safe FAILED status when the database is reachable. FAILED attempts
can be retried by the same CLI command. Database outages can prevent failure
status from being saved. Process interruption leaves a RUNNING claim: inspect the
provider job and database before manual recovery. Claims do not expire
automatically, avoiding duplicate paid calls. Partial runs remain unreferenced
for explicit reconciliation; no automatic destructive cleanup is performed.
MongoDB's per-record size limit still applies to a single extracted page or
source element. Very large provider output may fail persistence safely.

## Tests and honest verification

```bash
python -m pytest backend/tests -q
RESEARCHAI_TEST_MONGODB_URI=mongodb://localhost:27017 python -m pytest backend/tests -q
ruff check backend/services/document_processor backend/tests/test_parse_normalization.py backend/tests/test_llamaparse_client.py backend/tests/test_extraction.py backend/tests/test_extraction_cli_api.py backend/tests/test_extraction_integration.py backend/tests/test_llamaparse_live.py
```

Deterministic tests mock provider requests. MongoDB integration tests create/drop
only fresh `researchai_test_<uuid>` databases and use synthetic PDFs; extraction
provider output is explicitly mocked. Use a test deployment with database
creation/drop permissions.

The paid provider smoke test is separate and generates its own synthetic PDF:

```bash
RESEARCHAI_RUN_LLAMAPARSE_LIVE=1 python -m pytest backend/tests/test_llamaparse_live.py -q
```

Both explicit opt-in and a configured key are required. Do not enable this in
ordinary CI. No private research paper is used. On 2026-11-11 the full local
MongoDB suite passed **141 tests**, with **1 paid provider test skipped** because
no API credential was configured. This does not prove live cloud extraction
quality, paid-account access, or Atlas connectivity.

References: [Python quickstart](https://developers.llamaindex.ai/llamaparse/parse/getting_started/)
and [provider response format](https://developers.llamaindex.ai/llamaparse/parse/guides/response-format/).

## Markdown chunking (Prompt 7)

After extraction, run:

```bash
python -m backend.services.document_processor.chunk_cli DOCUMENT_ID
```

Optional --chunk-size/--chunk-overlap flags override CHUNK_SIZE/CHUNK_OVERLAP
(1200/150 characters). No provider credentials are used.
Read the active output through `GET /api/v1/documents/{id}/chunks`.
See the [chunking guide](../../../docs/markdown-chunking.md) for source mapping,
stable IDs, persistence/recovery and index compatibility.
