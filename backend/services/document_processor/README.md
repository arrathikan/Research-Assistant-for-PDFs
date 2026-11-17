# PDF ingestion

The RabbitMQ ingestion consumer calls these modules after the gateway safely
stores an original PDF. They also expose explicit operator CLIs from the root:

```bash
python -m backend.services.document_processor.main DOCUMENT_ID
python -m backend.services.document_processor.chunk_cli DOCUMENT_ID
python -m backend.services.document_processor.embed_cli DOCUMENT_ID
```

Parsing and embeddings consume configured provider quota. Prefer normal background
jobs for the user workflow; avoid concurrent manual work on an active job.

LlamaParse v2 uses the unified `llama-cloud` SDK, validates all one-based pages and
preserves Markdown/source elements with available geometry. Missing boxes are not
invented. Parsed runs publish only after complete persistence. Runtime prompts,
source schemas and parser metadata are required code, not temporary build notes.

LangChain heading splitting followed by recursive character splitting defaults to
1200 characters with target 150 overlap. Chunks retain source/page scope and stable
version identities. Voyage document vectors use a model/dimension profile and
content cache; changing the profile requires compatible re-embedding.

See [chunking/source mapping](../../../docs/markdown-chunking.md),
[hybrid search](../../../docs/hybrid-rag.md) and
[worker recovery](../../../docs/background-jobs.md). Deterministic tests mock paid
boundaries; opt-in integration/live tests are documented in [CI](../../../docs/ci.md).
