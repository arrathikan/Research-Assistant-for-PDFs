# Reference dashboard and full interaction-theme audit

## Implemented behavior

The previous library had a horizontal header, three inline statistics and article
rows without status filters or sorting. The reference requires a sidebar, four
compact cards and a table. The implementation reuses the existing document
metadata, selection, upload, deletion and Workspace components.

- A compact shared header keeps the user-selected book-logo PNG. Its bytes are
  unchanged (SHA-256 `4e419b0878e838ff7b3bc3cda453de62bbfb873979c970682aca202f1384a7da`).
  An SVG icon viewport and one native wordmark remove the previous duplicate
  tiny baked wordmark. The favicon still uses the supplied PNG.
- One navigation changes between compact mobile/tablet tabs and a desktop sidebar.
  Workspace remains discoverable but disabled until a document is selected.
- A welcome section uses only the document/magnifier region of the reference.
  The statistics use the supplied paper, ready and processing artwork. Original
  raster files are copied byte-for-byte; SVG viewports exclude baked labels and
  sample statistics. All visible counts and status labels are generated from
  actual uploaded metadata. Storage remains neutral, without fake profile data.
- The native table has filename, size, upload date, actual status and actions.
  It becomes stacked rows below 53rem of available container width. No duplicate
  desktop/mobile document list is rendered. Stable React keys preserve row state.
- Filename search, status filtering and newest/oldest/natural filename sorting
  combine without mutating the input document array. Search clear is labelled
  and returns focus. There are no unsupported author/year metadata assumptions.
- Processing counts include only PARSING/EMBEDDING/SUMMARIZING; pending and failed
  stay separate. Summary is enabled for READY; Chat also accepts completed
  embeddings. Filename/menu selection still opens the existing processing view.
- Upload validation/status/retry, safe delete confirmation and the five-section
  summary retain their integrations. Citations open the same retained PDF at its
  verified page, preserving chat, draft and zoom. Mobile PDF makes both header
  and navigation inert and restores them on dismissal.

## Why the earlier orange theme was incomplete

The active Tailwind palette was already orange. The remaining issues were state
coverage, native browser rendering and dormant source, rather than a cache-only
problem:

1. The palette had different soft/border shades, no pressed token and no shared
   semantic link/citation variants. Some hover rules overrode selected tabs or
   turned secondary buttons orange.
2. Inputs retained the gray control border on focus. A more specific global
   focus outline also overpowered the intended subtle field ring.
3. Chromium's native search-cancel icon could remain blue independently of the
   app palette. It is replaced by a labelled neutral button while preserving
   native search semantics and keyboard focus.
4. The unused SVG favicon fallback still contained `#2563eb`. Three untracked
   legacy prototype files also contained blue utilities, which Tailwind scanned.
   The SVG fallback is corrected in the change; exact color-only edits in those
   untracked files remain local, preserving their unrelated code and Git status.

The CSS import order is Tailwind base/components/utilities through one `index.css`
import in `main.tsx`. No separate dark theme or competing inline primary-color
mapping was found. Primary component states now share semantic tokens. No broad
`!important` override, cache workaround or recoloring of PDF source content was
introduced. Existing hidden/reduced-motion rules are unchanged.

| Token | Value | Use |
|---|---|---|
| `--brand-primary` | `#C6360A` | Primary controls, important links, focus border |
| `--brand-primary-hover` | `#A82E0A` | Hovered primary controls and selected-tab text |
| `--brand-primary-pressed` | `#8F2608` | Pressed primary controls |
| `--brand-soft` | `#FFF1EB` | Active tabs and citation chips |
| `--brand-border` | `#F0C9BB` | Subtle selected borders |

Surfaces remain #FAFAF9 / white, text #1C1917 / #57534E and borders #E7E5E4.
Unfocused field borders use an existing darker neutral for control contrast.
Secondary controls remain neutral; important linked actions receive the shared
link variant. Processing is amber, Ready green and destructive actions red.

## Guidance and accessibility applied

Installed layout, accessibility, forms, browser-control theming, responsive-table
and sortable-table guidance was consulted before implementation. Applied patterns
include native table/caption/scoped headers, labelled search/select controls,
container-responsive rows, intrinsic minimum sizes, numeric date sorting, natural
name comparison, stable DOM identity, status announcements, visible keyboard
focus, reduced-motion behavior and forced-color fallbacks. Sorting uses an
existing React state pattern and native select rather than adding an animation
or browser-specific sorting API. No dependency was added.

## Final source color audit

The audit searches frontend source, theme configuration, HTML and public SVGs
for blue/indigo utility names and the former blue primary shades, including
#2563EB, #1D4ED8, #3B82F6, #EFF6FF and associated shades.

| Remaining occurrence | Classification / action |
|---|---|
| Old blue/indigo utilities or primary hex values in first-party source | **0** after correction |
| The word “blue” in the search-cancel CSS comment | Explanation only; no color declaration |
| Third-party PDF.js styling and original paper content | Provider/document content; intentionally preserved |
| Native system menus and forced-color `Highlight` | User-agent/accessibility colors; intentionally not forced orange |

The source audit excludes generated dependency/build files from first-party
branding counts. Raster artwork and PDF pages are not blindly recolored. Browser
computed-style checks confirm primary #C6360A, hover #A82E0A, pressed #8F2608,
selected-tab background #FFF1EB/text #A82E0A, focused search/filter/chat/page-number
borders #C6360A and white cards. Success/processing/delete colors are separately
checked. Existing primary/citation text contrast checks pass at least 4.5:1.

## Verification — 2026-11-13

- Clean proposed source: **150 Vitest tests passed in 21 files**. The existing
  local checkout also passed **154 tests** including four unrelated untracked
  tests. Added eight focused cases for counts, combined filters/search, sort,
  action readiness and actual upload artwork stages.
- Strict application and browser TypeScript checks and production build passed.
  There is no configured standalone frontend lint command; type/build checks and
  the proposed patch's whitespace audit were used without adding a toolchain.
- **20 Chromium tests passed**. The two added scenarios check the reference
  dashboard, multiple metadata states, filtering/sorting, exact computed control
  colors, delete cancellation, full Workspace navigation, input focus, citations,
  accurate PDF text highlighting, zoom and no extra PDF load when toggled.
- Existing scenarios cover queued/processing/ready/failed and repeated uploads,
  keyboard modal dismissal, foreign/invalid citations, fallback highlights,
  retained conversation/summary/draft and PDF controls. No new page errors were
  detected in the added dashboard and cross-page scenarios.
- Checked **375, 768, 1024, 1280, 1440 and 1920px**. Before/after screenshots were
  saved privately, including populated library, Upload, Summary, Chat, upload and
  delete modals, desktop source split and mobile PDF. Inspected rendered crops,
  logo, responsive alignment and controls; root horizontal-overflow checks pass.
- Initial verification found an outdated zero-size expectation and two browser
  test-selector/geometry assumptions, which were corrected. An isolated-copy
  browser attempt failed because a dependency symlink placed the PDF worker
  outside Vite's serving boundary; using local copied dependencies resolved that
  test environment issue without changing application configuration.

## Limits and preserved boundaries

Browser API responses and PDF text are synthetic fixtures; this validates UI/API
contracts and real PDF rendering, not live provider/RAG quality. No paid parsing,
embedding, Ragas evaluation or backend change is part of this update. App-session
library persistence remains unchanged. Firefox/Safari, physical mobile devices
and screen readers were not tested; this is scoped accessibility verification.
Upstream PDF.js eval/build advisories remain. The original reference rasters add
about 2.4MB of cacheable image assets; no unsupported image-quality/performance
score is claimed. Previous RAG/dependency/release limitations remain in final QA.

Unrelated local edits and untracked prototype/test files are excluded from the
commit. The existing extra trailing newline in two intentionally redesigned
tracked files remains in the working tree but is excluded from the patch.

## Files changed

- `frontend/e2e/brand-redesign.spec.ts`
- `frontend/e2e/fixtures.ts`
- `frontend/e2e/research-workspace.spec.ts`
- `frontend/public/researchai.svg`
- `frontend/src/components/chat/CitedAnswer.tsx`
- `frontend/src/components/chat/DocumentChatPanel.tsx`
- `frontend/src/components/common/BrandIdentity.tsx`
- `frontend/src/components/common/CitationBadge.tsx`
- `frontend/src/components/common/DocumentStatusBadge.tsx`
- `frontend/src/components/dashboard/DocumentActions.tsx`
- `frontend/src/components/dashboard/DocumentCard.tsx`
- `frontend/src/components/layout/AppLayout.tsx`
- `frontend/src/components/layout/Navbar.tsx`
- `frontend/src/components/pdf/PdfViewerBoundary.tsx`
- `frontend/src/components/pdf/PdfViewerPanel.tsx`
- `frontend/src/components/summary/DocumentSummaryPanel.tsx`
- `frontend/src/components/upload/UploadStatusCard.tsx`
- `frontend/src/components/workspace/DocumentWorkspace.tsx`
- `frontend/src/index.css`
- `frontend/src/test/app-experience.test.tsx`
- `frontend/src/test/brand-identity.test.tsx`
- `frontend/src/test/design-system.test.tsx`
- `frontend/src/test/document-actions-upload-dialog.test.tsx`
- `frontend/src/test/layout.test.tsx`
- `frontend/src/test/navigation.test.tsx`
- `frontend/src/views/DashboardView.tsx`
- `frontend/tailwind.config.js`
- `frontend/src/assets/paper-status-reference.png`
- `frontend/src/assets/library-reference.png`
- `frontend/src/components/common/ResearchArtwork.tsx`
- `frontend/src/components/dashboard/library.ts`
- `frontend/src/test/library-reference.test.tsx`
- `frontend/e2e/dashboard-reference.spec.ts`
- `README.md`
- `docs/architecture.md`
- `docs/development-roadmap.md`
- `docs/frontend-brand-redesign.md`
- `docs/application-layout.md`
- `docs/dashboard-reference-theme.md`
