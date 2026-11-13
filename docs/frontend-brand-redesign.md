# ResearchAI brand and reading-workspace redesign

This report records the earlier reading-layout increment. The later
[reference-dashboard and complete state audit](dashboard-reference-theme.md)
supersedes its library metrics, header layout, soft-orange token and compact-logo
presentation. Its historical test counts describe that earlier increment.

## Cause and implementation

The existing frontend combined hardcoded blue/slate utility colors with blue
CSS tokens, large statistics cards and separate bulky summary cards. Updating
one color or max-width would leave inconsistent controls and unnecessary visual
weight. The upload modal, real processing status, deletion safeguards and optional
PDF session already worked and were reused.

The current design uses the supplied warm brand identity throughout the active
frontend. `tailwind.config.js` owns the brand scale; shared CSS tokens derive
from it. Primary is **#C6360A**, hover **#A82E0A**, light brand **#FCEAE5**,
page **#FAFAF9**, text **#1C1917 / #57534E / #78716C**, border **#E7E5E4**
and cards remain white. Existing success/error labels keep meaningful semantic
colors and icons. Shared buttons, fields, tabs, badges, loading, errors and focus
indicators use the same system.

The user's updated transparent 1254×1254 PNG is copied unchanged into
`frontend/src/assets/researchai-logo.png`. SHA-256:
`4e419b0878e838ff7b3bc3cda453de62bbfb873979c970682aca202f1384a7da`.
`BrandIdentity` supplies both navigation shells. The favicon references that same
asset. Vite hashes the asset URL in production, so replacing the logo changes its
cache identity. No logo regeneration, cropping, background editing or external
font/library was introduced. Visible brand text provides a readable name beside
the decorative image.

## Pages

- **Paper Library:** compact real counts/storage replace the three statistics
  cards. Paper rows display filename, real status, size/date, Summary/Chat
  shortcuts and the existing three-dot actions. Rows stack on narrow screens.
  Native search, empty results and confirmed deletion behavior are retained.
- **Upload:** simpler heading, focused drop target and one explanatory footer.
  The existing native modal still handles drag/drop, selection, validation,
  upload/retry and real queued/processing/Ready/failed states. No progress values
  or processing completion are fabricated.
- **Summary:** one continuous reading sheet with five divided sections, a serif
  research title shown once, author/abstract text, exact existing content and
  optional source passages. Section labels move beside content only when the
  pane is wide enough; split/mobile layouts stack them naturally.
- **Chat:** neutral user bubbles, a lighter answer area, aligned input, suggested
  questions (including contribution), familiar loading/retry and collapsed
  source passages. Numbered response references display actual `[Page N]`
  labels using the supplied citation metadata. Read-only references also show
  their actual pages; unknown references remain plain text.
- **Workspace/PDF:** retain 1440px app and 1200px reading boundaries, balanced
  16/24/32px padding and the existing optional 55:45 viewer layout. PDF remains
  closed by default. Citation clicks, correct-document checks, page/zoom,
  accurate highlight or quiet fallback, chat history and draft preservation
  continue through the same viewer. Mobile keeps its full-screen presentation.
- **Navigation:** shared supplied logo, warm active states and meaningful browser
  titles for Library, Upload and Workspace.

The backend API client, processing orchestration, MongoDB, retrieval, LLM calls
and Ragas logic were not changed. This is a presentation update, not an answer
quality improvement claim. Existing app-session library limitations remain.

## Accessibility and performance

Applicable color, layout, navigation, dialog and accessibility guidance was
consulted before editing. Implementation uses native search/dialog controls,
semantic headings, labels, `aria-current`, visible focus, reduced-motion and
forced-color support. Named CSS size containers respond to each actual library
or summary pane, avoiding viewport-only rules that break in split mode.

Browser checks measured at least 4.5:1 text contrast for primary buttons and
citation chips, confirmed the requested primary/hover colors, and exercised
keyboard dismissal/focus return and reduced motion. This is scoped testing, not
a WCAG certification or screen-reader audit. PDF code remains lazy-loaded and
retained across viewer toggles. No runtime or development dependency was added.
The logo stays byte-identical and is loaded as one shared built asset.

References consulted: [Vite asset imports](https://vite.dev/guide/assets) and the
installed color/layout/navigation/dialog/accessibility guidance. Existing native
control and safe renderer behavior was retained instead of adding a UI framework.

## Verification — 2026-11-13

- Proposed source (excluding unrelated existing local files): **142 Vitest tests
  passed in 20 files**, strict application/browser TypeScript and production build
  passed. Preserved local source: **146 passed** including four existing untracked
  tests. The two new unit cases check shared logo usage and page titles.
- **18 Chromium browser tests passed**, including four added checks for exact logo
  bytes/favicon, brand colors/contrast, responsive library search/actions,
  container-based reading layout, actual page labels and reduced-motion focus.
- Existing browser scenarios also cover upload failure/retry, queued/processing/
  completed states, invalid/foreign citations, repeated page navigation, exact
  highlighting/quiet fallback, retained chat/draft/summary/zoom and safe delete
  cancellation. Provider responses in this suite are synthetic; no paid AI
  evaluation or parsing request was made for this frontend redesign.
- Six widths checked: **375, 768, 1024, 1280, 1440 and 1920px**. Root overflow checks
  and desktop reading-width assertions passed. Screenshots of the new library,
  upload modal, summary and chat/PDF states were captured privately and inspected.
- The supplied PNG hash matches both the source asset and emitted production
  logo. Favicon URLs in the build resolve to the hashed asset. No new dependency
  or backend changes are included. There is no configured standalone frontend
  lint command; strict TypeScript/build and patch whitespace checks were used.
- Existing upstream PDF.js build warnings remain. Safari/Firefox, physical mobile
  devices and screen readers were not tested. Earlier RAG/dependency findings in
  [final QA](final-qa.md) remain separate from these interface checks.

## Files

- Tokens/assets: `frontend/tailwind.config.js`, `frontend/src/index.css`,
  `frontend/index.html`, `frontend/src/assets/researchai-logo.png`.
- Shared identity/layout: `components/common/BrandIdentity.tsx`, both existing
  `Navbar.tsx` components, `components/layout/AppLayout.tsx` and `SplitView.tsx`.
- Library/upload: `views/{DashboardView,UploadView}.tsx`,
  `components/dashboard/{DocumentCard,DeleteDocumentDialog}.tsx`,
  `components/upload/{UploadZone,UploadStatusCard}.tsx`.
- Reading/chat/PDF: `components/summary/DocumentSummaryPanel.tsx`,
  `components/chat/{DocumentChatPanel,CitedAnswer}.tsx`,
  `components/workspace/DocumentWorkspace.tsx`,
  `components/pdf/{PdfViewerPanel,PdfViewerBoundary}.tsx` and shared
  `CitationBadge`, `DocumentStatusBadge`, `EmptyState`, `LoadingSpinner`, `Modal`.
- Checks: `src/test/{brand-identity,answer-markdown,chat,layout,document-actions-upload-dialog}.test.tsx`
  and `e2e/brand-redesign.spec.ts` (frontend-relative paths).
- Living documentation: README, architecture, roadmap, earlier experience note
  and this design/verification report.
