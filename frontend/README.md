# ResearchAI frontend

React 18, strict TypeScript, Vite and Tailwind provide the orange ResearchAI paper
library, upload dialog and research workspace. The supplied book-logo PNG and
reference-derived illustration assets remain in use.

## Run and verify

Use Node.js 22. From this directory:

```bash
npm ci
npm run dev
npm test
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

Vite serves `http://localhost:5173`; the default API URL is
`http://localhost:8000/api/v1`. For a custom native gateway, export
`VITE_API_BASE_URL` before `npm run dev`, or put that public setting in
`frontend/.env.local`. Native Vite does not automatically read the root `.env`.
Only public configuration may use a `VITE_` prefix. Backend credentials must never
be exposed there. No separate frontend lint script is configured.

## Behavior

- The Dashboard keeps document references in session storage and refetches actual
  metadata on refresh. It supports filename search, status filters, sorting,
  download and confirmed deletion; it is not an authenticated account library.
- Upload accepts one PDF, preserving drag/drop and browser checks for type and
  25 MiB size. The backend also validates bytes/structure. Real upload and processing
  statuses control available actions; percentages and successful documents are not
  simulated. Processing retry uses the supported backend endpoint.
- Workspace presents the five-section saved summary and document-scoped chat.
  Opening/closing the PDF preserves chat, drafts, summary and PDF controls.
  Changing documents resets document-specific navigation.
- The PDF viewer is initially hidden and lazy-loaded. Toolbar and citations use
  the same React-PDF component. Source resolution checks scope/page/quote before
  navigation; reliable text/geometry highlights, otherwise the cited page opens.
  Desktop uses a split view and mobile uses a full-screen dialog.
- `predev` / `prebuild` copy matching PDF.js worker/fonts/CMaps locally. Generated
  `public/pdfjs/` is ignored; do not remove the preparation script.

Tests distinguish deterministic API fixtures from explicitly enabled live calls.
See [browser QA](../docs/browser-qa.md), [interface QA records](../docs/screenshots.md) and
[current review limitations](../docs/submission-review.md).
