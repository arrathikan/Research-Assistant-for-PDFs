# Prompt 15 final QA — 2026-11-13

Final QA and the demo guide are delivered. The verified public-paper flow works;
measured quality and dependency findings remain release limitations. This report
does not certify a public production deployment or universal RAG accuracy.

## Verified failure and fix

The existing public paper had completed LlamaParse extraction, 105 Markdown-aware
chunks and Voyage embeddings, but its summary job repeatedly reached terminal
failure. One bounded direct model diagnostic returned a quote with inserted
ellipses. Exact chunk/page/quote validation correctly rejected that output.

`grounded-summary-v2` requests short contiguous verbatim quotes and gives clearer
repair feedback. The profile hash changes with the workflow version. The
validator was not relaxed. A supported retry then completed on its first job
attempt and the saved summary was revalidated against its current source chunks.
The benchmark is Ready with all seven summary fields available and 13 verified
source records. Fresh paid parsing/embedding was not rerun in this stage; the
existing real artifacts were reused and the source PDF hash was checked.

The configured primary model was checked against the provider's current model
catalogue rather than assumed invalid. Neither model keys nor database secrets
were printed or committed. The unrelated other paper was not retried or deleted.

## Checks actually executed

| Check | Result | Boundary |
|---|---|---|
| Backend pytest | 474 passed; 4 paid checks deselected | Real disposable MongoDB/RabbitMQ integration; deterministic provider boundaries |
| Focused summary regression | 21 passed (included in full suite) | Elided quote remains rejected; bounded repair succeeds |
| Proposed frontend Vitest | 140 passed in 19 files | Clean source-equivalent copy excludes unrelated local files |
| Preserved local frontend Vitest | 144 passed in 20 files | Includes four existing untracked tests; not all are part of this branch |
| Strict TypeScript + build | Passed | App and browser-test types; lazy PDF build retained |
| Deterministic Chromium | 14 passed | Actual DOM/PDF.js; synthetic API fixtures; no provider calls |
| Opt-in live browser | 1 passed | Real CORS, multipart duplicate upload, Atlas summary/chat, PDF page 3 and mobile viewer |
| Docker smoke | Passed; test resources cleaned | Rebuilt non-root services, Nginx proxy, assets/fonts, upload/dedup/GridFS/status/delete |
| Ruff | Backend lint and scoped Python formatting passed | No new frontend lint framework introduced |
| Ragas | 18 responses, 58 values, 30 skips, 2 errors | Offline paid scoring; partial report with 18 assistant source reviews |
| Report/export regressions | 25 passed (included in backend suite) | New report schema, review hashes, metric states and source PDF binding also validated |
| npm audit | 10 findings: 3 critical, 5 high, 2 moderate | Existing dependency graph; audit counts include transitive/advisory effects |

GitHub Actions [run 43383787551](https://github.com/arrathikan/Research-Assistant-for-PDFs/actions/runs/43383787551)
passed all three jobs for QA code commit `81064f5`: backend, frontend/browser and
Docker full-stack smoke. The subsequent handoff commit contains documentation and
measured public benchmark artifacts.

The local runtime used Python 3.13; rebuilt Docker and GitHub CI target Python
3.12/Node 22. There is no configured standalone frontend ESLint pass. The existing
PDF.js build warning and upstream Python deprecation warnings remain visible.

The browser matrix checked 375, 768, 1024, 1280, 1440 and 1920px. Root overflow,
1100–1200px desktop summary cards, 55:45 split and mobile close/focus behavior
passed. Screenshots were captured outside Git; representative desktop/mobile
views and the live source highlight were visually inspected. Chat messages,
draft, summary, page and zoom survived viewer toggles without a second PDF load.
Invalid/foreign sources were safely rejected. Menu/delete cancellation and
upload retry/repeated selection were also checked. No uncaught JavaScript page
errors occurred in those scenarios. Safari/Firefox, screen readers and physical
mobile devices were not tested.

The Docker worker was gracefully drained while idle, then restored using the
smoke-tested v2 image; its previous image tag was retained. Native gateway/worker
processes were reloaded with the same fix. Unrelated app containers/data were
preserved. Every one of the 13 initially modified/untracked files was hash-checked
unchanged and excluded from commits.

## Evaluation and release limits

[Full measured Ragas follow-up](../evaluation/reports/2026-11-13-final-qa/README.md)
retains context, answers, source pages, configuration, actual metric errors and
hash-bound reviews. Overview traces now prove saved-summary reuse. Both overview
context-recall metrics returned invalid/missing values and remain null/error.
Seven answers still have incomplete inline claim support; three also have
attribution/answer issues. Broad saved-summary claims can likewise cite only part
of their supporting evidence. No overall accuracy or hybrid-superiority claim
is made, and independent human review is not claimed.

The dependency audit still flags the existing React-PDF/PDF.js/canvas/tar chain
and Vite/Vitest/esbuild/tinypool tools. The viewer already sets
`isEvalSupported: false`, the documented workaround for the specific
[PDF.js advisory](https://github.com/mozilla/pdf.js/security/advisories/GHSA-wgrm-67xf-hhpq).
That setting is not a clean dependency audit or a substitute for upgrading.
Resolve and retest these dependencies before public deployment; no forced major
upgrade was hidden inside the QA change. Keep development servers local.

Existing deployment also lacks authentication, authorization and public TLS.
Dashboard documents are held in app-session state; a full reload needs selecting
or reuploading the same source to rejoin its stored record. The optional Prompt
3.2 visible connection indicator remains deferred; tested HTTP health is liveness,
not full dependency readiness. A pure sparse-only retrieval benchmark is not
claimed. These are explicit follow-ups rather than fabricated completion claims.

## Files changed by final QA

- Summary: `backend/services/summary_service/{models,workflow}.py`,
  `backend/tests/test_summary_workflow.py`.
- Browser tooling: `frontend/e2e/{fixtures.ts,research-workspace.spec.ts,live-demo.live.ts}`,
  `frontend/playwright.config.ts`, `frontend/tsconfig.e2e.json`,
  `frontend/package.json`, `frontend/package-lock.json`, `frontend/vite.config.ts`.
- CI/privacy: `.github/workflows/ci.yml`, `.gitignore`, `frontend/.dockerignore`.
- Documentation: `README.md`, `docs/{architecture,development-roadmap,ci,structured-summary,browser-qa,final-qa,demo-guide}.md`,
  `evaluation/README.md`, `docs/rag-evaluation.md` and
  `evaluation/reports/2026-11-13-final-qa/`.

See [browser QA](browser-qa.md) for reproducible local/CI commands and separate
paid live selection, and [the demo guide](demo-guide.md) for setup, walkthrough,
interview explanations and honest recovery steps. Feature commits are pushed
for review; no merge or force push is performed.
