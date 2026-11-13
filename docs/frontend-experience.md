# ResearchAI frontend experience

Current branding and page presentation are documented in the
[warm-brand redesign](frontend-brand-redesign.md). The blue-palette descriptions
and measurements below record the earlier implementation.


## Problems and resulting behavior

The shared 1440px frame from the previous increment was retained. Remaining issues
were inconsistent small typography, low-contrast metadata, undersized controls,
click-only document titles, a bare chat composer and PDF toolbar, repeated loading
placeholders and a mobile suggestion list competing with its input.

The existing local Dashboard shell also started with hardcoded sample documents
marked READY; its Chat and Summary shortcuts shared a handler that always chose
Summary. The shell is now integrated into App with an honest empty library, actual
upload metadata, SHA-256 library deduplication and the requested shortcut tab.
No backend endpoint or processing contract changed.

## Guidance actually consulted

Before implementation, the installed Modern Web Guidance instructions were read,
then the current CLI was used to search and retrieve these guides:

- accessibility: semantic HTML, heading order, native actions, visible focus,
  meaningful labels, restrained live announcements and inert modal backgrounds;
- forms: persistent input labels, linked feedback, 16px fields, IME-safe Enter;
- tabs: real tab/tabpanel semantics, selected state and keyboard interaction;
- toolbar: labeled, grouped native PDF actions with usable targets;
- motion: opt-in animation, reduced-motion behavior, no unnecessary spatial effects;
- performance: dynamic imports for heavyweight optional code;
- size-aware-styling and card: article/header/footer semantics and container-width
  adaptation, preserving source order and a usable stacked fallback.

The installed instructions emitted an older-version notice; the references were
retrieved using modern-web-guidance@latest. No skill installation or application
dependency was added. Limited-support focusgroup APIs and polyfills were avoided;
portable explicit ARIA tabs with ArrowLeft/Right, Home and End are used instead.
PDF controls remain native tab stops grouped with a descriptive label rather than
claiming composite-toolbar keyboard behavior.

Primary references checked alongside the guides:
[React lazy](https://react.dev/reference/react/lazy),
[React state preservation](https://react.dev/learn/preserving-and-resetting-state),
[WCAG 2.2 target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).
The guide source is [Modern Web Guidance](https://github.com/GoogleChrome/modern-web-guidance).

## Design system and each page

CSS variables centralize the requested blue, hover, text, surface, border, success
and error colors. Shared ui-button, ui-field, ui-card, ui-tab and ui-badge styles
supply consistent sizing, corners, borders and modest shadows. Fields are 16px;
primary controls are at least 44px high. Citations remain compact with at least
24px targets. Focus uses a visible offset outline with a forced-colors fallback.
Skeletons and spinners respect reduced motion, including source-scroll behavior.
No external fonts, UI framework or new component dependency were introduced.

- Dashboard: clearer heading and introduction, honest derived statistics, actual
  documents, accessible search, and responsive grids. Document articles adapt to
  their own container width: compact rows when wide, stacked cards when narrow.
  Titles work with a keyboard. Summary and Chat actions open their actual tab.
- Upload: a focused 1024px column, obvious Choose PDF action, one accessible file
  control, associated validation messages and aligned selection/status cards.
  Existing deduplication, drag/drop, size/type checks, job states and retry rules
  remain authoritative; no percentage or READY state is invented.
- Workspace: selected filename and friendly status, consistent tabs and PDF action.
  Summary and Chat stay mounted during tab/viewer changes. The PDF is closed by
  default and uses the existing 55/45 split or mobile full-screen overlay.
- Summary: five aligned sections, numbered headings, readable paragraph lengths,
  loading skeletons and concise real waiting/error states. A failed selected paper
  does not poll indefinitely or tell the user to upload another PDF.
- Chat: readable bubbles and safe Markdown, two starter questions and five optional
  question ideas, a labeled composer, pending feedback, explicit retry and polite
  message-log semantics. Suggestions only fill the input; sending is explicit.
  Sources remain collapsed, without scores or internal identifiers.
- PDF: larger grouped controls, accessible labels, retained page/zoom and quiet
  page-only fallback. The global header is inert during the mobile overlay.
  Code is lazy-loaded once, with a boundary that offers the original PDF if the
  optional viewer cannot load; it does not replace or discard the conversation.
- Common states: consistent empty/error components and reduced-motion loading.
  The Vite placeholder icon is replaced by a small code-native ResearchAI book.

## Responsive and functional verification

Actual CSS viewports checked: 375, 768, 1024, 1280, 1440 and 1920px. Dashboard,
Upload selection/status, Summary, Chat and the optional PDF were checked for
shared alignment, readable sizing and horizontal overflow.

| Viewport | Outer frame | Upload | Closed Summary/Chat | PDF when open |
|---|---:|---:|---:|---|
| 375px | 375px | 343px | 343px | Full-screen |
| 768px | 768px | 720px | 720px | 55/45 split |
| 1024px | 1024px | 960px | 960px | 55/45 split |
| 1280px | 1280px | 1024px | 1200px | 55/45 split |
| 1440px | 1440px | 1024px | 1200px | 55/45 split |
| 1920px | 1440px | 1024px | 1200px | 55/45 split |

Gutters remain 16px mobile, 24px tablet and 32px desktop. There was no page-level
horizontal overflow. Dashboard metrics stack on mobile; document actions wrap.
The main scroll owners are unchanged; intentional PDF zoom may scroll its canvas.
Screenshots were captured and inspected outside Git, with a further refinement
made after the first mobile chat screenshot exposed the crowded suggestion list.

Live QA rejected a non-PDF, reused an existing completed 11-page PDF through
upload deduplication, loaded its saved five-part summary, and sent one real chat
question. Suggestions filled/focused the input before explicit sending. Chat
citations opened pages 4 and 5. Reopening preserved page 6 at 125% zoom, the
conversation and unsent draft. Mobile opening focused Close PDF; closing restored
focus to the source and removed background inertness. A page-only highlight
fallback occurred without technical warning text; a final summary source produced
four exact-text highlight rectangles on page 5. These checks do not establish
RAG answer accuracy or claim a new evaluation result.

## Automated checks and performance

- Baseline local frontend: 113 tests passed.
- Final local frontend: **131 tests passed** across 19 files.
- Isolated proposed frontend: **127 tests passed** across 18 files; four existing
  untracked wrapper tests are excluded from the proposed commit.
- Both final strict TypeScript/production builds passed.
- No standalone frontend lint script is configured. Scoped/staged whitespace
  checks were used alongside TypeScript; no lint pass is claimed.
- The final live verification tab recorded no console errors or warnings.
- Focused coverage includes honest initial library, duplicate uploads, correct
  Summary/Chat shortcuts, suggestions, retry, failed summaries, keyboard tabs,
  PDF code-failure containment and page/zoom retention through all six widths.
  Existing upload, citation, invalid-document/page and highlight tests still pass.

Both the original and proposed frontends were built with the same installed
compiler/bundler dependencies. Original initial JavaScript was 575.00kB
(169.95kB gzip); the redesigned initial chunk is approximately 203kB (62kB gzip).
The approximately 369kB PDF chunk and 1087kB worker are deferred until requested.
This measures build output, not Core Web Vitals or a network-speed guarantee.

Checked design-palette contrast: primary blue/white 5.17:1, secondary text/white
4.76:1, main text/background 17.06:1, error/white 4.83:1 and field border/white
3.11:1. This is a targeted check, not a complete WCAG certification or a screen
reader/user study. No new libraries were installed for audits or testing.

## Limits

The document library remains scoped to the current App session; there is no new
server-side listing API or cross-reload library persistence. Existing chat history
uses the established session-storage conversation pointer and backend history.
PDF page/zoom/draft retention applies within the selected Workspace session;
leaving it or changing documents resets document-specific UI as before.

Exact highlighting still depends on matching extracted text or verified geometry.
Existing RAG/Ragas quality limits and upstream PDF.js eval warnings remain.
A native Chrome Dashboard screenshot was also inspected to cross-check the
in-app browser presentation. Safari/Firefox, real mobile devices and a full
assistive-technology audit were not tested.

## Files changed

- `frontend/index.html`
- `frontend/src/App.tsx`
- `frontend/src/components/Navbar.tsx`
- `frontend/src/components/chat/CitedAnswer.tsx`
- `frontend/src/components/chat/DocumentChatPanel.tsx`
- `frontend/src/components/common/EmptyState.tsx`
- `frontend/src/components/common/ErrorMessage.tsx`
- `frontend/src/components/common/LoadingSpinner.tsx`
- `frontend/src/components/dashboard/DocumentCard.tsx`
- `frontend/src/components/layout/AppLayout.tsx`
- `frontend/src/components/layout/Navbar.tsx`
- `frontend/src/components/pdf/PdfViewerPanel.tsx`
- `frontend/src/components/summary/DocumentSummaryPanel.tsx`
- `frontend/src/components/upload/UploadStatusCard.tsx`
- `frontend/src/components/upload/UploadZone.tsx`
- `frontend/src/components/workspace/DocumentWorkspace.tsx`
- `frontend/src/index.css`
- `frontend/src/test/chat.test.tsx`
- `frontend/src/test/layout.test.tsx`
- `frontend/src/test/navigation.test.tsx`
- `frontend/src/test/pdf-workspace.test.tsx`
- `frontend/src/test/summary.test.tsx`
- `frontend/src/views/DashboardView.tsx`
- `frontend/src/views/UploadView.tsx`
- `frontend/src/components/common/DocumentStatusBadge.tsx`
- `frontend/src/components/pdf/PdfViewerBoundary.tsx`
- `frontend/src/test/design-system.test.tsx`
- `frontend/src/test/app-experience.test.tsx`
- `frontend/public/researchai.svg`

Documentation: README.md, docs/architecture.md, docs/development-roadmap.md and this guide.

The existing untracked frontend/src/test/workspace.test.tsx was adapted locally to
query the new tab roles and remains untracked. Unrelated backend, API, test setup
and legacy component edits were preserved. The existing local App navigation was
retained and integrated, with its sample records removed as described above.
