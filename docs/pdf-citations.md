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
passed. Native PDF canvas/worker behavior still needs browser verification.
