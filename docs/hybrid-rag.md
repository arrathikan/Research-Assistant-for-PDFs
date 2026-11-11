# Document-scoped hybrid RAG (Prompt 10)

Retrieval uses direct Voyage query embeddings, Atlas Vector Search, MongoDB
Search with explicit BM25 similarity, and Python reciprocal rank fusion (RRF).
There is no local fake semantic-search fallback. Ordinary local `mongod` supports
storage tests but does not provide these search stages.

## Atlas indexes

After parsing, chunking and embedding a stored PDF, show the required definitions:

```bash
python -m backend.services.rag_service.indexes
```

To explicitly create missing indexes on the configured `chunk_embeddings`
collection (requires a search-enabled MongoDB deployment):

```bash
python -m backend.services.rag_service.indexes --create
```

Index creation is asynchronous. Wait until both indexes are queryable. Existing
incompatible indexes are never updated or dropped: review them or select new
names. The vector index uses the configured embedding dimensions and cosine
similarity; the keyword index uses `lucene.standard` with BM25. Both index the
same document/chunk-set/embedding-profile filters.

Every query pre-filters by document, active chunk set and embedding profile.
Results are checked against canonical current chunks and their content hashes.
A generation change during retrieval invalidates the result. Both indexes must
be ready before paying for a query embedding. Retrieval failures return safe
errors rather than silently degrading to a different algorithm.

Dense and keyword candidates run through LangChain RunnableParallel. RRF adds
`1 / (constant + rank)` from each unique ranking; raw BM25/vector scores are not
mixed. Ties use chunk order and ID deterministically. Ranking scores are not
accuracy/confidence estimates.

| Setting | Default |
| --- | --- |
| `KEYWORD_SEARCH_INDEX_NAME` | `chunk_keywords_v1` |
| `VECTOR_SEARCH_INDEX_NAME` | `chunk_embeddings_v1` |
| `RAG_CANDIDATE_K` | 20 per branch |
| `RAG_CONTEXT_K` | 6 after fusion |
| `RAG_RRF_CONSTANT` | 60 |
| `RAG_CONTEXT_BYTES` | 32000 UTF-8 bytes for source context |
| `RAG_HISTORY_TURNS` | 6 |

Verification so far: 14 deterministic retrieval/index tests passed. Atlas itself
has not been verified: the local environment still points at local MongoDB.
Answer generation, persistence and frontend integration are described below.

References: [MongoDB vector query documentation](https://www.mongodb.com/docs/vector-search/query/aggregation-stages/vector-search-stage/),
[MongoDB Search string/BM25 configuration](https://www.mongodb.com/docs/search/indexes/field-types/string-type/).

## Grounded answers and offline evaluation traces

The ordinary LangChain chain builds a bounded prompt, invokes the configured
OpenRouter model, and validates structured claims. Each claim needs a quote from
one retrieved chunk's actual page span. Invalid/missing citations fail the turn;
no answer is saved. Empty retrieval skips the LLM and returns a polite abstention.
The model can also abstain when nonempty context does not answer the question.
History is context for interpretation, never factual source evidence.

`answer_with_trace` returns a typed public response plus an internal evaluation
trace with question, answer, actual selected contexts/IDs/pages, citations,
measured latency and model/retrieval/chunk configuration. Public responses exclude
retrieval text/configuration traces. There is no Ragas call or fabricated score
in the request path. Claim entailment still requires manual/offline evaluation;
quote identity checks are not proof of scientific correctness.

Source/history JSON is bounded by `RAG_CONTEXT_BYTES`. Old history is removed
before excluding whole source chunks that do not fit; source text is never cut
mid-chunk. Traces record only the chunks actually supplied to the model.

## Chat API and saved history

POST `/api/v1/documents/{id}/chat` accepts `message` and an optional existing
`conversation_id`. GET `/api/v1/documents/{id}/chat/{conversation_id}` returns
up to the last 100 completed turns. Conversation IDs are scoped to document,
parse, chunk set and embedding profile; another document cannot reuse them.
Concurrent sends in one conversation return 409. Each successful database insert
contains the question, answer and private trace atomically, so failures cannot
leave half a turn. Sequence numbers preserve ordering even for equal timestamps.

API responses contain verified citation IDs, chunk/document/page references,
quotes and an explicit unsupported-answer flag. Retrieval traces remain private
in `chat_turns` and through the internal `chat_with_trace` function. History
returns public turn data only. Real measured pipeline latency includes retrieval
and generation, not full network delivery. Generation/source changes are checked
before storing and returning; old-generation history is never returned for a new
generation. No Ragas evaluation runs during a chat request.

A crashed process can leave a conversation busy: inspect it before manually
recovering its claim. No automatic lock stealing or exactly-once guarantee across
lost HTTP responses is implemented. Completed turns and traces contain research
text and should follow the deployment's retention/access policy; authentication
and multi-user authorization have not been introduced by this stage.

HTTP errors: 404 unknown document/conversation, 409 not-ready/busy/changed sources,
422 invalid request, 503 unavailable storage/provider/search. There is no silent
BM25-only or fake semantic fallback when Atlas is unavailable.

## Frontend and commands

The real chat panel sends questions to the public endpoint, displays pending,
failed and insufficient-evidence states, shows source quotes and recovers saved
history. Only the conversation ID is stored in sessionStorage, separately per
document; chat text is not persisted in browser storage. A document switch
ignores late answers. Sending failures never create a simulated assistant reply.
Citation callbacks preserve IDs/document/chunk/page/quote for Prompt 11's viewer.
The local workspace redesign is preserved and connected locally; the committed
App gets the same panel without committing unrelated local layout/PDF-viewer work.

For a parsed/chunked document, prepare embeddings, create indexes, then ask:

```bash
python -m backend.services.document_processor.embed_cli DOCUMENT_ID
python -m backend.services.rag_service.indexes --create
python -m backend.services.rag_service.main DOCUMENT_ID "What method does this paper use?"
```

Wait for both search indexes to be queryable. HTTP example:

```bash
curl -X POST http://localhost:8000/api/v1/documents/DOCUMENT_ID/chat \
  -H 'Content-Type: application/json' -d '{"message":"What method does this paper use?"}'
```

Use the returned conversation_id for subsequent turns/history. Retrieval and
answers may consume provider credits. The primary model is configurable through
OpenRouter. Voyage reranking is configured but not enabled by this RRF pipeline.
RabbitMQ orchestration and interactive PDF source highlighting remain later stages.

## Verification

Normal deterministic checks mock paid/search boundaries and test real MongoDB
persistence using disposable databases. Enable live checks explicitly:

```bash
RESEARCHAI_RUN_ANSWER_LIVE=1 python -m pytest backend/tests/test_rag_live.py::test_live_openrouter_grounded_answer -q
# Configure RESEARCHAI_TEST_ATLAS_URI locally; it must permit disposable test databases.
RESEARCHAI_RUN_RAG_LIVE=1 python -m pytest backend/tests/test_rag_live.py::test_live_atlas_hybrid_chat_document_isolation -q
```

The Atlas test uses synthetic parsed artifacts, real Voyage/Atlas/OpenRouter,
creates only a uniquely named researchai_test database and removes it afterwards.
It does not parse a private PDF. Normal CI skips it even if keys are present.

Current working-copy verification: **302 backend tests passed, 4 live tests
skipped**; production frontend build and **36 tests passed**. The separately
opted-in live OpenRouter answer check **passed** on synthetic text and verified
its source citation and stated result. The full live Atlas test was **not run**:
MONGODB_URI remains a local MongoDB address. No retrieval-quality/Ragas scores or
claims that hybrid retrieval outperforms semantic retrieval are made.

Independent staged-PR verification: **302 backend tests passed, 4 skipped**,
frontend production build and **32 tests passed**. The working copy has 4
additional preserved workspace tests (36 total). All staged credential/whitespace
and scoped Ruff checks passed. User confirmed Atlas is not yet set up; see the
[Atlas setup guide](atlas-setup.md) to complete the remaining live verification.
