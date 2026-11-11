# Markdown-aware chunking — Prompt 7

## Run it

Install the backend dependencies and complete parsing for the document first.
The chunking stage is local and requires MongoDB access but no LlamaParse,
Voyage or LLM API key. It does not parse an unparsed PDF automatically.

```bash
python -m backend.services.document_processor.chunk_cli DOCUMENT_ID
python -m backend.services.document_processor.chunk_cli DOCUMENT_ID --chunk-size 1200 --chunk-overlap 150
curl http://localhost:8000/api/v1/documents/DOCUMENT_ID/chunks
```

Environment defaults are `CHUNK_SIZE=1200` and `CHUNK_OVERLAP=150`, in Python
characters, not tokens or bytes. Size must be positive and overlap must satisfy
0 <= overlap < size. CLI flags override the environment for that invocation.
Restart an older gateway process with the current dependencies/code to expose
the new read endpoint and use the updated index initialization.

`GET /api/v1/documents/{id}/chunks` returns the complete active chunk set. It
returns 409 before chunking/current parsing is complete, 404 for unknown IDs,
422 for malformed IDs and 503 for storage failure. Reads never start processing.
The endpoint currently returns the full set without pagination.

## How splitting works

MarkdownHeaderTextSplitter detects headings h1 through h6 and carries their
hierarchy across PDF pages. Fenced-code headings do not become research sections.
Paragraphs with the same heading context are grouped, while new heading sections
stay separate. RecursiveCharacterTextSplitter then uses paragraph, line, word
and character boundaries to keep content within the configured limit.

Overlap applies inside a section; boundary choices can yield less than the
configured overlap. Small tables retain their Markdown rows. Oversized tables
or rows may split to respect the hard character cap. LangChain normalizes
whitespace/indentation; this is not a byte-preserving Markdown formatter.
The parsed Markdown and original PDF remain authoritative.

## Page/source attribution

Explicit page markers are inserted from the parsed page numbers before splitting
and removed before chunks are saved. Missing/ambiguous marker coverage is an
error. A chunk can span a continuing section on multiple pages and keeps:

- document_id, parse_run_id and deterministic chunk_set_id/id;
- ordered chunk_index, heading_path and deepest section_title;
- first/last page plus exact contributing page_numbers;
- per-page evidence text and start/end offsets into the chunk content;
- matched source element IDs, available boxes, coordinate units and page sizes.

Blank pages are not cited as evidence. Offsets describe chunk text, not guessed
positions in the PDF or original Markdown. Source matching normalizes whitespace
and requires a unique supporting location on the source page. Source elements
intersecting the relevant text range are preserved, including their coordinate
metadata. Ambiguous repeated text or unavailable coordinates use page attribution
without invented element/box links. Exact PDF highlighting comes later.

IDs include document content/source metadata, parse provenance, chunk settings,
actual splitter version and algorithm version (`markdown-pages-v1`). Repeating
the same input/configuration preserves IDs. Changing parsed content, coordinates,
configuration or splitter/algorithm version intentionally creates another set.
Update the algorithm version when changing chunk semantics. Token counts remain
null; this stage does not claim character counts are embedding-token counts.

## Persistence and recovery

`chunk_document(parsed, parse_run_id, config)` is the reusable pure chunking
function. `chunk_stored_document(database, document_id, settings)` reads a
published parse, claims chunking, upserts a new immutable set and conditionally
publishes active_chunk_set_id. `read_document_chunks` filters by that pointer,
checks count/order and requires the set to match the active parsed version.

Stable-ID writes use set-on-insert, preserving previously stored records. A new
configuration keeps old output available until the replacement set is fully
published. A partial failure keeps the old active pointer; retry completes the
same deterministic set without duplicate records. Source isolation and parse
version are checked before publication. Abandoned partial sets remain for manual
reconciliation; no chunk records are deleted automatically.

Metadata tracks chunking_status/chunked_at. Success leaves the overall document
PENDING for later embeddings/summary generation; no embedding is performed and
no document is marked READY for chat. A running claim blocks other writers. A
process interruption or parse-version change can leave a running claim; inspect
the document and unpublished output before manual recovery. Rechunking a document
actively in a later pipeline stage is blocked.

## Legacy index compatibility

The unique index now covers `(document_id, chunk_set_id, chunk_index)`. The old
`document_chunk_index` over `(document_id, chunk_index)` cannot support immutable
generations. Initialization removes that known legacy index only when its
collection is empty. It does not delete records.

Populated legacy data causes an explicit initialization error. Stop old writers,
back up and review the legacy records, and create/verify the new unique index
before an operator removes the old index. Existing legacy records can be kept
for audit; only newly published active sets are returned by the chunk reader.
Do not blindly drop indexes on a database used by older services.

## Verification

```bash
python -m pytest backend/tests -q
RESEARCHAI_TEST_MONGODB_URI=mongodb://localhost:27017 python -m pytest backend/tests -q
python -m backend.services.document_processor.chunk_cli --help
```

On 2026-11-11: **178 passed, 1 skipped** with disposable local MongoDB. The skipped
test is the paid live parser smoke test from Prompt 6; no paid parser was called.
Offline: **160 passed, 19 skipped** (18 database tests plus the paid parser test).
Tests use real LangChain splitters and synthetic parsed artifacts, and cover
headings, overlap, page continuation, source boxes, stable IDs, invalid settings,
real storage/reuse/reconfiguration, partial writes, parse changes, document
isolation and both empty/populated legacy-index handling.

Provider extraction quality and Atlas connectivity remain unverified. Chunking
validation does not establish retrieval or answer quality; those are measured in
later retrieval and offline Ragas stages.

References: [Markdown header splitter](https://reference.langchain.com/python/langchain-text-splitters/markdown/MarkdownHeaderTextSplitter)
and [recursive splitter](https://reference.langchain.com/python/langchain-text-splitters/character/RecursiveCharacterTextSplitter).

Frontend regression: **22 tests passed** and the full TypeScript/Vite production
build passed in the current working checkout. Existing uncommitted workspace
implementation remains outside this stage's commits.
