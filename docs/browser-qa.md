# Browser QA

Playwright is an explicitly approved development dependency. Production images
serve only built assets; the browser runner is not a frontend runtime dependency.
The tests reuse the existing application, actual PDF.js renderer and native
browser controls. No second PDF implementation or UI framework was added.

## Deterministic checks

```bash
cd frontend
npm ci --no-audit --no-fund
npx playwright install chromium
npm test
npm run typecheck
npm run test:e2e
npm run build
```

The default suite starts its own loopback Vite server on port 4173, uses isolated
browser contexts and intercepts every API request. An unexpected endpoint fails
the fixture. It generates a seven-page PDF in memory: no provider keys, live
papers, MongoDB or paid calls are needed. Vitest excludes `e2e/**`; a separate
TypeScript configuration checks the browser code. CI installs Chromium and runs
this default suite after unit checks/build, before container verification.

The 14 browser checks cover:

- Upload keyboard dismissal and focus return; drag-and-drop file selection.
- Queued, running, completed and failed processing, with no premature readiness.
- Upload retry and clearing previous file state when starting another upload.
- PDF hidden initially, page 7 then page 2, exact text highlight and quiet page
  fallback when verified extraction does not match rendered PDF text.
- Rejected/foreign/invalid sources remain safe; rejected source resolution does
  not navigate to an unverified target.
- Page/zoom, chat messages, draft and summary remain intact across viewer toggles.
- Menu/delete-dialog cancellation twice, with focus restored and no deletion.
- Dashboard, upload, summary, chat and viewer at 375, 768, 1024, 1280, 1440 and
  1920px; no root overflow, desktop summary cards 1100–1200px, 55:45 split and
  mobile close/focus behavior.
- No uncaught JavaScript page errors in these scenarios.

Tests follow user-facing names and roles, browser assertions and isolated state.
Accessibility/dialog/layout guidance informed the keyboard, focus, modal and
intrinsic-width checks. No timing sleeps or invented processing percentages are
used. See [Playwright practices](https://playwright.dev/docs/best-practices),
[web-server configuration](https://playwright.dev/docs/test-webserver) and
[isolated browser options](https://playwright.dev/docs/test-use-options).

## Explicit live public-paper check

This additional check **can consume model credits** and writes one standard public
benchmark chat turn. It is excluded from the default suite and CI. It requires
native gateway/workers, configured providers/Atlas and an already completed
current summary. The source must be the exact reviewed 17-page public paper
[Lost in the Middle](https://aclanthology.org/2024.tacl-1.9/); its SHA-256 is checked
before upload. Obtain the PDF yourself and keep it outside version control.

```bash
cd frontend
RESEARCHAI_LIVE_QA=1 \
RESEARCHAI_QA_PDF=/absolute/path/to/the/reviewed-paper.pdf \
RESEARCHAI_QA_DOCUMENT_ID=YOUR_24_CHARACTER_DOCUMENT_ID \
npm run test:e2e -- --workers=1
```

The live server uses `http://localhost:5173` and the real API at
`http://localhost:8000/api/v1`, exercising actual multipart upload and CORS. Both
ports must be available for the intended services; an existing frontend is never
reused or stopped automatically. The check verifies deduplication, current saved
summary, the 2,655-query answer, document-scoped citation navigation, actual PDF
rendering, mobile viewer, draft/history preservation and unchanged job generation.
It reuses processing artifacts; it does not rerun paid parsing or embedding.

By default Playwright uses downloaded Chromium. To check installed Chrome with an
isolated test profile, set `PLAYWRIGHT_CHROMIUM_CHANNEL=chrome`; `chromium` uses the
full downloaded Chromium build. No personal browser profile is accessed.

For optional screenshots, set `RESEARCHAI_QA_SCREENSHOTS` to an existing absolute
output directory. The six-width checks capture dashboard/upload/summary/PDF;
the live check captures actual summary/citation/mobile views. Browser outputs
under `frontend/test-results/` and `frontend/playwright-report/` are ignored by Git
and excluded from Docker contexts. Live and deterministic runs have separate
output directories. Keep traces/screenshots private; they can contain papers and
conversation text. CI does not upload these artifacts.

## Verified scope and limits (2026-11-13)

The deterministic suite passed all 14 tests in downloaded Chromium 158. An earlier
13-case version also passed in installed Chrome. The one opt-in live test passed
against the real gateway, Atlas and configured models. Responsive screenshots and
the live page-3 highlight were visually inspected. A disposable Docker smoke test
also passed, including actual upload/dedup/GridFS/status/delete and the Nginx proxy.

Screen-reader testing, Safari/Firefox and physical mobile devices were not tested.
Viewport checks are browser emulation; they are not a WCAG certification. Synthetic
API cases prove interface behavior, not provider quality. See the final QA and
Ragas reports for measured answer/citation limitations and outstanding dependency
advisories.
