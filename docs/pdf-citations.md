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
covered deterministically. React-PDF rendering/highlighting follows next.
