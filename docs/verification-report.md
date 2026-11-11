# Local verification — 2026-11-11

## Verified behavior

- Gateway health, metadata, document status and allowed-origin CORS preflight.
- A synthetic PDF uploaded through the actual browser UI returns success and
  remains PENDING. Uploading identical bytes again returns the same document ID.
- A non-PDF file with a .pdf extension is rejected. A valid retry succeeds.
- The downloaded original matches uploaded bytes and SHA-256 exactly.
- The browser exercise leaves exactly one metadata record and one GridFS file.

## Automated checks

- Complete backend suite against isolated local MongoDB: **87 passed**. Includes
  concurrent writes, request limits and original-file round trips.
- Complete frontend suite in the current working checkout: **22 passed**.
- `npm run build`: TypeScript and Vite production build passed.
- Ruff checks passed for the storage fix and related regression tests.
- One existing Starlette/AnyIO deprecation warning remains in backend tests.

## Corrections

Stored-document timestamps now use UTC millisecond precision so upload and
metadata-read responses match BSON dates. The dashboard EmptyState import path
and unused test imports were fixed. The local workspace test checks accessible
section headings rather than assuming the separate section number is part of
the heading text. The local workspace's unused icon import was removed.

## Scope

These results validate Prompt 5 uploads and storage. New documents remain
PENDING; parsing, embeddings, generated summaries, real RAG chat and source
highlighting are not validated as working backend features yet. Existing sample
library/workspace content is a frontend demonstration.

The frontend results include the existing local workspace implementation. Those
previously untracked workspace files remain uncommitted; the verification fixes
do not publish that unrelated work. Atlas connectivity was not tested. Live
checks used synthetic data in an isolated, loopback-only local MongoDB database.
