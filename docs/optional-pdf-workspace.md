# Optional PDF workspace

The previous desktop grid always allocated two equal columns and mounted the
PDF even before it was requested. Mobile PDF visibility was coupled to the active
tab. Summary sources were static text and could not use chat's citation path.

The Workspace now starts with a single content column. View Original PDF opens
the existing React-PDF viewer; Close PDF hides it and restores centered summary/
chat content. Clicking a valid chat or summary citation opens that same viewer
and requests its verified source page. The active summary/chat tab is unchanged.
An explicit legacy initialTab=pdf remains an intentional open request.

## State and source navigation

Simple local React state owns visibility and the selected citation. The PDF is
mounted only on first request and retained while hidden, preserving its own page,
zoom and loaded document. Summary/chat panels remain mounted, preserving loaded
summary, messages, conversation identity and unsent input. A new selected document
gets a new session, so old pages, zoom, sources and late replies cannot leak into
it. Browser reloads or leaving/unmounting the Workspace start a new PDF session.

The Workspace rejects foreign-document and invalid page selections. The existing
citation API then verifies source identity, current generation and exact canonical
excerpts. The viewer applies page navigation only after checking actual PDF page
count; an unavailable page leaves the last valid page visible with a friendly
error. Exact text and verified-coordinate highlights are retained. Page-only
fallback has no technical highlighting warning.

Saved summaries already expose source metadata. The new Web Crypto helper creates
the existing citation SHA-256 from those fields, then follows the same resolver
and viewer path. Localhost/HTTPS support secure hashing; unavailable hashing gets
a friendly fallback. No backend endpoints or RAG behavior changed.

## Responsive and accessible behavior

At 768px and above, an open PDF uses 55% summary/chat and 45% PDF. Each pane owns
its scroll area; the PDF controls remain outside its scrolling canvas. Below
768px, the viewer fills the viewport as a modal with a close control. Keyboard
focus stays inside, Escape closes it, and focus returns to the opening source or
button. Hidden content has no visible PDF toolbar or placeholder.

Measured closed-content widths and open layouts:

| Actual viewport | Closed content | Open layout |
|---|---:|---|
| 375px | 343px | Full-screen PDF, about 375px wide |
| 769px (tablet target ~768) | 721px | About 397px / 325px |
| 1280px | 768px | About 598px / 490px |
| 1440px | 768px | About 598px / 490px |

The outer readable page boundary stays at 1152px. No page-level horizontal
overflow was observed. Intentional zoom can scroll within the PDF viewport.

## Verification

- Baseline frontend: 99 passed.
- Final preserved workspace: **110 passed**. Isolated proposed frontend:
  **106 passed**, excluding four existing untracked wrapper tests.
- Both production builds and strict TypeScript checks passed.
- Backend regression: **463 passed, 4 optional live tests skipped**, using a
  disposable database and isolated broker queues with simulated provider calls.
- Scoped whitespace checks passed. No separate frontend lint script is configured.
- Full Python Ruff check reports four existing I001 import-order errors in
  backend/shared/__init__.py, backend/tests/test_evaluation_schemas.py,
  backend/tests/test_gateway_health.py and backend/tests/test_shared_models.py.
  Those files are byte-identical to origin/main and were not changed.
- Existing PDF.js eval/bundle-size and upstream deprecation warnings remain.

Automated coverage includes initial hidden state, no initial PDF URL lookup,
manual open/close, retained PDF node/page/zoom, full-width recovery, repeated
page-7/page-3 citations, same-document scope, bad pages, foreign documents, late
responses on document changes, preserved chat/draft/summary, canonical summary
hashes, missing secure hashing, mobile focus containment/return, exact highlighting,
region highlighting and quiet missing-highlight fallback.

Live QA used existing stored papers, including one with a completed five-part
summary; duplicate uploads reused them and started no processing jobs. Real chat
sources opened pages 3 and 8. Closing/reopening retained page 9 at 125% zoom and
both chat messages. A live summary source opened page 5 of the correct 11-page PDF,
using one viewer, while the summary text remained unchanged. On mobile, closing
returned focus to the exact Methodology source button. Sources/Supporting passages
started collapsed. Responsive checks covered approximately 375, 768, 1280 and
1440 CSS pixels.

## Limits

Highlighting depends on compatible extracted text or trusted geometry. Navigation
does not establish semantic correctness of every generated claim; the existing
Ragas/manual evaluation limitations still apply. This UI refinement makes no new
answer-accuracy claim. PDF navigation is retained for the current selected-document
Workspace session; it is reset on document changes or full page reload.
