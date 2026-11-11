# Summary service

Runs a controlled LangGraph workflow over published, page-attributed Markdown
chunks. It produces the five required research-summary sections through the
configured OpenRouter gateway and verifies source IDs, pages and quoted text.

```bash
python -m backend.services.summary_service.main DOCUMENT_ID
```

Parsing/chunking must be completed first. This is an explicit job, not yet a
RabbitMQ consumer. GET `/api/v1/documents/{id}/summary` reads the published result
without a paid model call. See [the complete guide](../../../docs/structured-summary.md)
for generation, retries, missing information, versioned storage and limitations.
