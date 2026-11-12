# Shared application layout

## Cause and scope

Workspace had already gained a 1440px frame, but the default PageContainer and
both navigation components still selected a 1152px limit for other pages.
Upload then nested a 768px column inside that frame. The differing parent and
child boundaries made Dashboard/Upload narrow and changed header alignment when
switching pages. Root width, dynamic viewport height and scroll ownership were
already correct; there was no global CSS override or empty active sidebar to remove.

All active views were inspected: Dashboard, Upload and the document Workspace
with Summary, Chat and the optional PDF. The document list lives in Dashboard;
its document actions open that same Workspace. The existing local
DocumentWorkspaceView delegates to DocumentWorkspace. No additional active detail
route needed a separate layout. The unused legacy SplitView was left unchanged.

## Shared and page changes

- PageContainer now always uses a centered 1440px limit, with 16px mobile,
  24px tablet and 32px desktop gutters. Both navigation implementations use it too.
  The page-specific wide option is no longer needed.
- Dashboard uses that wider frame. Its existing three derived statistics stack
  on mobile; its auto-fit document grid collapses unused tracks. Accessible
  section and search labels support navigation and regression tests. Document
  data, counts, storage calculations, filtering and selection are unchanged.
- Upload uses a focused 1024px inner limit for its title, drag/drop selection,
  selected file and processing status. Validation and processing logic are unchanged.
- Summary and Chat retain their aligned 1200px column. Summary cards fill it,
  paragraphs retain 100ch limits, and answer bubbles retain 90ch limits.
- The PDF stays unmounted until requested. The existing 55/45 split, mobile modal,
  citation resolution, independent scrolling and retained page/zoom are unchanged.

No dependencies, APIs, backend code, RAG processing or evaluation settings changed.
Pre-existing local work was preserved and excluded from the feature commit.

## Responsive verification

Measurements used actual CSS viewport widths in the running local application.
Dashboard, Upload selection/status, saved Summary, Chat and the open PDF were
checked at every width below.

| Viewport | Shared outer frame | Upload column | Closed Summary/Chat | Open PDF layout (assistant / PDF) |
|---|---:|---:|---:|---|
| 375px | 375px | 343px | 343px | Full-screen 375px PDF |
| 768px | 768px | 720px | 720px | 396px / 324px |
| 1024px | 1024px | 960px | 960px | 528px / 432px |
| 1280px | 1280px | 1024px | 1200px | About 669px / 547px |
| 1440px | 1440px | 1024px | 1200px | About 757px / 619px |
| 1920px | 1440px | 1024px | 1200px | About 757px / 619px |

Navigation/page boundaries matched; the focused upload states aligned with their
heading; all five summary cards matched the Workspace toolbar. Conversation and
input edges matched at all six sizes. A real answer remained about 794px wide on
larger screens, rather than stretching to the full conversation width. No
page-level horizontal overflow was observed. Larger screens intentionally retain
balanced margins after the shared cap. Intentional PDF zoom may scroll inside
the viewer.

Live QA reused an existing completed paper through SHA-256 deduplication; it
started no parsing or embedding jobs. A summary source opened page 5. A real chat
answer supplied citations that opened pages 4 and 10 in the same viewer.
Manual navigation to page 6 at 125% zoom survived closing/reopening. Chat and
summary text stayed unchanged; mobile source opening focused the close control.

## Automated checks

- Baseline frontend: 112 tests passed.
- Preserved local frontend: **113 tests passed**.
- Isolated proposed frontend: **109 tests passed**, excluding four pre-existing
  untracked wrapper tests.
- Both strict TypeScript checks and production builds passed.
- Layout coverage checks both header variants, shared frame/tab navigation,
  upload width and Dashboard counts/filtering/selection. Existing tests cover
  upload states, citations, PDF controls, hidden initial viewer, invalid sources,
  document changes and preserved summary/chat state.
- Scoped whitespace checks passed. No standalone frontend lint script is configured.
- Existing PDF.js eval and bundle-size build warnings remain.

These are frontend layout checks. They make no new RAG accuracy claim and do not
rerun the offline evaluation or change existing sample-library persistence.
