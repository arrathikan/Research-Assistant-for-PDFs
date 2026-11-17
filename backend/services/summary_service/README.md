# Summary service

A deterministic LangGraph workflow generates five research-summary sections from
published page-attributed chunks. OpenRouter returns schema-constrained drafts;
the server validates current source IDs, pages and quotes before publication.
Missing facts stay explicitly unavailable. Validation does not prove scientific
correctness and can reject inaccurate full-paper model outputs.

Normal uploads schedule the RabbitMQ summary consumer after ingestion. An explicit
operator command is also available from the repository root:

```bash
python -m backend.services.summary_service.main DOCUMENT_ID
```

Do not run it concurrently with an active job. `GET /api/v1/documents/{id}/summary`
reads a saved current result without a paid call. See [the summary guide](../../../docs/structured-summary.md)
for bounded repair, versioned publication and readiness semantics.
