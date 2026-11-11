# PDF citations (Prompt 11)

## Verified source contract

Chat citations retain citation/document/chunk/page identifiers and the supporting
quote. They now also retain parse/chunk generation identifiers, source element
IDs, page dimensions and available bounding boxes. Citation IDs are deterministic
source identities, not authorization tokens.

POST `/api/v1/documents/{id}/citations/resolve` accepts a citation identity, selected
document, chunk, page, quote and optional source-generation IDs. It reads canonical
current chunks, checks identity/page/quote membership and rechecks the active
source generation. Client-supplied geometry is not accepted. Unknown documents
return 404, invalid references 422 and stale/not-ready sources 409. No paid model
or parser request is made by resolution.

New LlamaParse v2 extractions preserve the documented top-left origin and box
rotation metadata. Existing stored boxes remain available. Only unambiguous source
elements with known units/origin, zero box rotation and valid bounds are eligible
for a region overlay. Unknown provider coordinates, rotated elements and missing
frames must not be guessed. Text matching/page navigation handle those cases.
[Provider coordinate conventions](https://developers.llamaindex.ai/llamaparse/parse/guides/response-format/).

Backend verification: **322 tests passed, 4 optional live tests skipped** with
disposable local MongoDB. Source identities, wrong documents/pages/quotes, stale
generations, canonical geometry, missing/unknown coordinates and API errors are
covered deterministically.

## Viewer behavior

`components/pdf/PdfViewerPanel.tsx` streams the uploaded GridFS PDF through
React-PDF. Page counts come from the PDF itself. Controls include page selection,
previous/next, 50–200% zoom, reset, retry and opening the original PDF. The worker,
CMaps and standard fonts are served locally from the installed PDF.js version;
`predev`/`prebuild` prepares the ignored assets. No CDN is required.

After canonical source resolution, the viewer jumps to the source page. It first
matches the quote uniquely across rendered text spans/line breaks and draws
native DOM Range rectangles without changing the PDF text layer. Whitespace,
soft hyphens and compatibility ligatures are normalized. If that fails, confirmed
source boxes can provide a region overlay only when the PDF frame, units, origin
and rotation agree. Otherwise the page and quote remain visible with an explicit
message that an exact highlight is unavailable. Repeated text is not guessed.
Zoom/resize rerender and recompute overlays; old-page overlays are hidden while
rendering. Late resolver responses and references to another document are ignored.

Viewer verification: frontend **67 tests passed** in the working copy, including
23 text/geometry tests and 8 viewer tests with a mocked renderer. Production build
passed. Native PDF canvas/worker behavior was subsequently verified below.


## Citation navigation

Inline `[n]` references and always-visible page buttons in chat open the matching
source. Quote disclosures can remain collapsed. Unknown numeric references stay
plain text; model strings are rendered as React text, never injected HTML.
`DocumentWorkspace` keeps one PDF instance across summary/chat/PDF tabs. On small
screens a citation reveals the PDF pane, and returning to chat keeps the current
conversation. Repeated source clicks reverify and reopen that page. Switching
documents clears the selected citation and ignores previous pending results.

Integration verification: **325 backend tests passed, 4 optional live tests
skipped**; frontend **73 tests passed** and build passed in the working copy.
Backend tests used disposable local MongoDB, with provider boundaries mocked.
The local dashboard redesign is preserved separately from the committed minimal
App integration.


## Browser verification — 2026-11-12

The isolated production build was exercised in the in-app browser with a
three-page synthetic PDF, real local MongoDB/GridFS, the actual gateway routes,
and canonical parsed/chunk source records. Retrieval, embedding and completion
provider boundaries were simulated for this UI check; no paid calls were made.
The synthetic page without selectable text simulated an OCR-source mismatch;
this check does not establish LlamaParse OCR accuracy.

Observed results:

- The original uploaded PDF rendered through the local PDF.js worker with its
  actual three-page count and a selectable text layer.
- An inline citation opened page 2 and highlighted its quote across two lines.
- At 125% zoom, both highlight rectangles were recomputed over the source text.
- Navigating to page 3 removed the old overlay; clicking the same page-2 citation
  again reopened page 2 and restored the highlight.
- A source on the page without selectable text opened page 3, displayed the
  quote and the explicit exact-highlight-unavailable message, with no overlay.
- At a 390×844 viewport, clicking the citation revealed the PDF pane and matched
  text at the new page width. Returning to chat retained both turns. There was
  only one PDF viewer instance. The viewport override was reset afterward.
- No browser console warnings or errors were captured in the final check.

The local API was reloaded with the citation route and its Atlas connection
was pinged successfully. The application database contained no documents during
that runtime check, so an existing-document HTTP read was not performed.
No Atlas data was seeded, migrated or removed for this browser check.

Final verification of the isolated commit content: **69 frontend tests passed**
and production build passed; backend regression: **325 passed, 4 optional live
checks skipped**. The local redesign also passed its four workspace checks.
Build output retains the installed PDF.js package's eval/bundle-size warnings;
PDF parsing is configured with `isEvalSupported: false`. Dependency upgrades and
bundle optimization were outside this stage.

## Try it locally

1. Start the gateway with the project's ignored `.env`, then run `npm run dev`
   from `frontend` so the local PDF assets are prepared.
2. Upload a PDF. Complete parsing, chunking, embeddings and summary generation with the existing
   processing commands; open the workspace when the document is ready. Automatic
   queued processing belongs to Prompt 12.
3. Ask a question that the PDF can answer. Click its `[n]` reference or page
   button. Confirm the quoted source, page number and visible highlight state.
4. Zoom, navigate away and click the citation again. On a narrow screen, return
   to AI Chatbot to continue the same conversation.
5. When extraction differs from selectable PDF text, inspect the page and quote.
   A region overlay is a source region rather than an exact text match. Ambiguous
   text, missing coordinates or incompatible page geometry use the stated
   page-only fallback. Do not interpret that state as a verified text highlight.

These checks validate navigation and source contracts. Scientific answer quality,
manual benchmarks and Ragas metrics remain later stages; no evaluation scores
are claimed here.
