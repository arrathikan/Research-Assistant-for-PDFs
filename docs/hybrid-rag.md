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
Answer generation, persistence and frontend integration follow next.

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
