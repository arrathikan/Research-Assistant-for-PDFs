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
