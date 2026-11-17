# Shared backend modules

The gateway and workers share Pydantic settings/models, safe logging, synchronous
PyMongo/GridFS storage, embedding helpers and the OpenRouter completion client.
Configuration comes from the root ignored `.env` or process environment.

## Storage initialization

From the repository root with backend dependencies installed:

```bash
python -m backend.shared.database
```

`connect_database(settings)` bounds connection/selection/socket timeouts and closes
the client on exit. `ensure_indexes` initializes ordinary MongoDB indexes; explicit
Atlas search-index creation is a separate [command](../../docs/hybrid-rag.md).
Synchronous driver work belongs in workers or synchronous FastAPI handlers.

`store_pdf` computes SHA-256 and uses a unique metadata index to resolve concurrent
uploads. A losing write removes only its own candidate GridFS file. BSON IDs become
strings at the API boundary. GridFS/metadata writes are not one atomic transaction;
ambiguous failures may need backed-up operator reconciliation. Never delete an
original just because a request timed out.

Versioned chunks use `document_chunk_set_index`. If a populated legacy collection
still has `document_chunk_index`, initialization fails safely and retains its data;
review/migrate with old writers stopped. Domain modules add their own generation
indexes. There is no automatic destructive data migration.

Tests use isolated databases when `RESEARCHAI_TEST_MONGODB_URI` is explicitly set.
See [CI](../../docs/ci.md) and [architecture](../../docs/architecture.md) for storage
collections, deletion ownership and the limitations of liveness/CORS.
