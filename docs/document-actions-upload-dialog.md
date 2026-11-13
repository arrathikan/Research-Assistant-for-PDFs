# Paper actions and upload dialog

Previously, the Dashboard had no delete action or cleanup endpoint. Upload
selection and status appeared directly below the page's drop zone. Navigating away
unmounted the upload controller. The redesign reuses the upload validation, API
client and processing state machine inside a native dialog.

## Dashboard and deletion contract

Each paper has an accessible actions menu: Open Workspace, View Original PDF for
a stored document, and Delete Paper. Delete opens a labelled native confirmation
with Cancel initially focused. Cancel/Escape are safe; confirmation disables
repeat submissions and closing during cleanup. Errors keep the card and allow an
explicit retry. Only success removes the card, updates counts/storage/search,
clears selected Workspace state and removes its browser conversation pointer.
Late metadata responses cannot re-add a deleted ID.

`DELETE /api/v1/documents/{document_id}` returns an empty **204** after acknowledged
cleanup. It is idempotent, including requests for an absent ID. Invalid IDs return
**422**, an active/uncertain short write returns **409**, and incomplete cleanup
returns **503**. Retrying DELETE completes partial cleanup. A failed response does
not imply that no data was removed.

Cleanup uses the exact document ID, including historical BSON ID fields, for:

- Original GridFS file/chunks and document metadata.
- `parsed_pages`, `source_elements`, `chunks`, `chunk_embeddings`.
- `summary_runs` and legacy `summaries`.
- `chat_conversations`, `chat_turns` and legacy `chat_messages`.
- `processing_jobs`, including its durable outbox record.

Global indexes and the content-addressed numeric `embedding_vectors` cache are
shared resources and remain. Other documents and their files are preserved. A
file referenced by another document remains. Inconsistent file ownership fails
for operator review. The existing application has no authentication/ownership
layer; this endpoint retains that single-user trust boundary. Multi-user deployment
requires authorization before exposing deletion.

## Workers and partial failures

A conditional metadata update marks `deletion_state=DELETING` before cleanup.
Readers hide that document; SHA-256 deduplication rejects an incomplete deletion.
Document-specific inserts/upserts in parsing, chunking, embedding snapshots,
summary publication, chat persistence and job scheduling acquire a short
`document_write_token`. It covers database writes only, never provider calls.
Deletion returns 409 while a writer owns the guard. Once marked, new writes and
late provider results cannot recreate document-specific records. Late broker
messages are acknowledged without starting work. No queue or global index is purged.

Metadata is deleted last, retaining the GridFS ID and barrier on partial failure.
GridFS is not transactional. Retry removes leftover chunks even after its file
entry was removed. Cleanup is idempotent. An already sent provider request cannot
be recalled; its late result is rejected at persistence.

**Deployment:** restart the gateway, dispatcher and every worker with this version
before using Delete. Old workers do not recognize the barrier. A crash or ambiguous
connection/write-concern failure can retain a write token. It has no expiry because
an outstanding server write might still finish. Stop the relevant writer, inspect
and reconcile its writes, then conditionally remove that exact token before
retrying DELETE. Never unlock a live/uncertain writer based only on elapsed time.

## Upload lifecycle

The main page has one clean dialog trigger/drop area. Clicking opens the existing
picker inside the dialog; dropping a file opens it preselected. The shared
validation helper checks PDF type/extension, one nonempty file and 25 MiB. Browse,
replace, remove, Cancel and upload remain keyboard accessible.

The existing API request shows Uploading, then real stored-document and job states:
Uploaded/Queued, Processing, Ready or Failed. Done and Go to Dashboard are available
as soon as storage is confirmed. Open Workspace appears only after job completion,
current summary retrieval and complete embeddings confirm readiness. Existing job
rules govern retry/start controls. No percentages or database IDs are displayed.

App keeps the upload controller mounted across navigation. Closing the dialog
aborts neither the active request nor queued processing. Storage success immediately
upserts the session library by SHA-256. While the dialog is closed, App polls real
metadata every three seconds for non-ready papers. Failed reads retain the last
confirmed state; polling includes failed metadata because an automatic job retry
can progress later. Another upload clears prior UI state and stops prior UI polling,
without cancelling backend work.

The library remains session-scoped; there is no new listing API or cross-reload
persistence. Closing the browser itself can interrupt an active HTTP upload.

## Guidance and accessibility

Consulted the installed Modern Web Guidance's current native-dialog and
menu/popover guidance. Native `showModal()` provides the top layer, background
inertness, focus containment and return. Closing before unmounting preserves focus.
Labels, visible Cancel/Close controls, live status messages, reduced-motion spinners
and destructive button styles reuse existing tokens. No dialog library or custom
focus trap was introduced.

Menus progressively use native popovers, command invokers, focusgroup and CSS anchor
positioning. Feature-detected fallbacks provide outside dismissal, arrows/Home/End,
Escape, focus return and viewport-clamped placement. Tests model missing JSDOM
dialog methods; browser checks exercise native focus and keyboard behavior.

## Verification

- Frontend: **144 local / 140 isolated tests passed**, including 12 new dialog/menu/delete,
  background upload, metadata refresh and late-response cases.
- Backend: **471 passed, 6 optional live/broker checks skipped**. Disposable MongoDB
  databases exercise actual GridFS cleanup, other-document/cache preservation,
  idempotency, write guards, partial cleanup and late parsing/embedding/job writes.
  No existing user paper was deleted.
- Both local and isolated TypeScript/production builds passed. Full backend Ruff lint passed; all 20 changed Python files pass format checks.
  Four pre-existing import-order errors were sorted in a separate style increment. There is no configured frontend lint script.
- Browser: a real synthetic PDF uploaded to a separate local QA database, returned
  a durable queued job, appeared in Dashboard, and remained one card after a duplicate
  upload. Closing the modal left the library usable. No READY result was simulated
  and no paid parsing, embedding or summary request was made for this verification.
- Upload and Dashboard were checked at 375, 768, 1024, 1280, 1440 and 1920 CSS pixels
  with no horizontal page/dialog overflow. Dialog widths were 343px on mobile and
  608px on larger screens. Desktop/mobile screenshots were inspected.
- Native menu arrows/Escape, delete Cancel focus/return and mobile confirmation
  worked. Permanent deletion was verified in isolated API tests, not by confirming
  deletion of a user paper in the browser.

The upstream PDF.js build `eval` warning remains. RAG model settings, retrieval,
provider calls and evaluation behavior are unchanged.

## Changed files

- `README.md`
- `backend/gateway/documents.py`
- `backend/gateway/main.py`
- `backend/services/document_processor/chunk_storage.py`
- `backend/services/document_processor/embedding_storage.py`
- `backend/services/document_processor/extraction.py`
- `backend/services/jobs/dispatch.py`
- `backend/services/jobs/lifecycle.py`
- `backend/services/jobs/processor.py`
- `backend/services/jobs/store.py`
- `backend/services/rag_service/service.py`
- `backend/services/summary_service/storage.py`
- `backend/shared/__init__.py`
- `backend/shared/document_lifecycle.py`
- `backend/shared/storage.py`
- `backend/tests/test_chunk_storage.py`
- `backend/tests/test_document_deletion.py`
- `backend/tests/test_evaluation_schemas.py`
- `backend/tests/test_extraction.py`
- `backend/tests/test_gateway_health.py`
- `backend/tests/test_shared_models.py`
- `docs/architecture.md`
- `docs/development-roadmap.md`
- `docs/document-actions-upload-dialog.md`
- `frontend/src/App.tsx`
- `frontend/src/components/common/Modal.tsx`
- `frontend/src/components/dashboard/DeleteDocumentDialog.tsx`
- `frontend/src/components/dashboard/DocumentActions.tsx`
- `frontend/src/components/dashboard/DocumentCard.tsx`
- `frontend/src/components/upload/ProcessingProgress.tsx`
- `frontend/src/components/upload/UploadStatusCard.tsx`
- `frontend/src/components/upload/UploadZone.tsx`
- `frontend/src/components/upload/selection.ts`
- `frontend/src/index.css`
- `frontend/src/services/api.ts`
- `frontend/src/test/app-experience.test.tsx`
- `frontend/src/test/design-system.test.tsx`
- `frontend/src/test/document-actions-upload-dialog.test.tsx`
- `frontend/src/test/layout.test.tsx`
- `frontend/src/test/setup.ts`
- `frontend/src/test/summary-upload.test.tsx`
- `frontend/src/test/upload-api.test.ts`
- `frontend/src/test/upload-integration.test.tsx`
- `frontend/src/views/DashboardView.tsx`
- `frontend/src/views/UploadView.tsx`
