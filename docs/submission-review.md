# Interview submission review — 14 November 2026

**Retention update — 15 November 2026:** Historical screenshots and raw QA artifacts were subsequently removed from the repository. The review below records the state observed on 14 November; its findings and limitations remain unchanged. See [interface QA records](screenshots.md).

The documentation and repository cleanup are complete locally. **Do not describe
this as a fully security-ready or fully validated release.** Existing dependency
advisories and broader model-quality/review limitations remain. No commit, push,
merge, history rewrite or repository-setting change was made for this review.

## Scope and repository state

- Project: `ResearchAI – Research Assistant for PDFs`.
- Remote: [arrathikan/Research-Assistant-for-PDFs](https://github.com/arrathikan/Research-Assistant-for-PDFs).
- Working branch: `codex/live-e2e-qa-20261113`, HEAD `8abae18`.
- Remote default branch: `main`, fetched at `d43071b` (merge of PR #29).
  Its tracked tree matches this feature branch's committed tree. These cleanup
  changes remain local and uncommitted; GitHub does not contain them yet.
- Initial inventory: 306 tracked files, including 49 Markdown documents. Source,
  configuration, tests, runtime prompts, branding and retained evaluation evidence
  were classified before cleanup. No tracked generated/credential file was found.
- The existing eight modified and five untracked source/test files were preserved
  byte-for-byte. The ignored local `.env` was also preserved byte-for-byte.

## Cleanup and preservation

Only verified untracked generated files were deleted, with recovery copies outside
the repository: **418 files, 8,678,320 bytes (approximately 8.3 MiB)**.

| Removed category | Files |
| --- | ---: |
| macOS `.DS_Store` files | 4 |
| Python bytecode/cache files under `__pycache__` | 181 |
| Ruff cache files | 32 |
| pytest cache files | 6 |
| Regenerable `frontend/dist` build outputs | 195 |

No tracked source file was deleted. `node_modules`, virtual environments, npm
lockfile, dependency declarations, Docker/CI configuration, supplied logos and
illustrations, tests, runtime LLM prompts, evaluation data/reports, and meaningful
history remain. No local uploaded PDF or existing database data was selected.
The generated PDF.js asset preparation script and its dependency assets remain.

Temporary stage-by-stage instructions and contradictory append-only narratives
were replaced in the README, architecture and implementation-status pages.
Remaining stage labels were removed from operational guides. Dated QA records
were retained and indexed as historical evidence; their old test counts are not
presented as current results. Retaining evidence avoids concealing model failures
or contribution history merely to make the repository look cleaner.

### Manual review: preserved deliberately

- Existing untracked legacy workspace files: `ChatMessageItem.tsx`,
  `PdfViewerPanel.tsx`, `SummarySection.tsx`, `workspace.test.tsx` and
  `DocumentWorkspaceView.tsx`. These are pre-existing user work, not this change.
- Existing tracked local edits in `backend/gateway/__init__.py`, common citation/
  empty/error components, `dashboard/DocumentCard.tsx`, `services/api.ts`,
  `test/setup.ts` and `test/smoke.test.ts`. They are not part of this cleanup.
  Seven contain pre-existing trailing blank-line warnings, which were preserved.
- `frontend/public/researchai.svg`: an older branding asset retained rather than
  deleting potentially useful artwork. The active favicon uses the supplied PNG.
- `evaluation/benchmark_dataset.json`: unverified legacy five-case scaffold still
  used by schema tests. The active benchmark is `datasets/rag_test_cases.json`.
- Existing design screenshots and dated QA artifacts: retained for provenance,
  rather than guessing that historical evidence is disposable.
- No root project license was found. The owner should choose a license if public
  reuse is intended; no legal permission or contributor identity was invented.

## Documentation and setup changes

The root README now provides overview, implemented features, stack, architecture,
RAG flow, native setup, environment names, usage, checks, directory structure,
limitations and verified author details. Short sections link to deeper guides.

Architecture now describes a modular backend with separate API/worker processes,
not a collection of unimplemented HTTP microservices. It covers immutable source
publication, scoped chat/history, safe deletion, offline evaluation and actual
provider boundaries. A documentation index distinguishes current operations from
historical reports. The screenshot gallery labels actual orange UI captures and
public-paper excerpt scope; concept artwork is not presented as application QA.

Two setup pitfalls were verified and documented:

1. On a fresh database, requesting a search index before `chunk_embeddings`
   exists returns MongoDB code 26. [Atlas setup](atlas-setup.md#6-initialize-storage-and-search)
   now provides explicit idempotent collection initialization. `--create` requests
   indexes; it does not wait for queryability. Without `--create`, the CLI prints
   definitions rather than live readiness. No runtime source change was needed.
2. Native Vite reads its own environment files/process variables, not the root
   `.env`. [Frontend setup](../frontend/README.md) now explains exporting a custom
   public API URL or using `frontend/.env.local`. The default URL works unchanged;
   Docker's Nginx build uses the same-origin API path.

The safe `.env.example` contains placeholder provider keys, local-only broker
credentials, current provider comments and ResearchAI attribution. Removed unused
`APP_HOST`; documented `APP_PORT` with Compose port settings. Local credentials
were not copied into it. `.gitignore` now also covers named virtual environments,
coverage variants, Hypothesis caches and common backup/temporary files; source,
`.env.example`, fixtures and the npm lockfile remain eligible for tracking.

Fresh native dependency installation from an empty machine was **not** rerun.
Commands were checked against actual entry points and used with installed tools;
container builds and runtime smoke checks passed. There is no Python dependency
lockfile; existing constraints were preserved rather than silently upgrading them.

## Technology claims checked against source

| Claim | Implementation evidence |
| --- | --- |
| FastAPI gateway / schemas | `backend/gateway/main.py`, document/chat/processing/citation routes and Pydantic contracts |
| SHA-256 / GridFS | `backend/shared/storage.py`, upload validation, storage/dedup integration tests |
| RabbitMQ workers | `backend/services/jobs/`, `backend/shared/broker.py`, real broker integration tests |
| LlamaParse | `document_processor/llamaparse_client.py`, normalization and page/source storage |
| LangChain chunking | `document_processor/chunking.py`: Markdown headings then recursive character splitting; 1200/150 default, not token counts |
| Voyage embeddings | `backend/shared/voyage.py`, model/dimension profiles and embedding storage/cache |
| Atlas Vector Search + BM25 + RRF | `rag_service/indexes.py` and `retrieval.py`: `$vectorSearch`, `$search` text with BM25, rank fusion and scope checks |
| LangChain answers | `rag_service/chain.py`, selected canonical passages, validated citations and saved history |
| LangGraph summary | `summary_service/workflow.py`: deterministic identify/generate/validate/advance/combine/save graph, bounded repair |
| Metadata / follow-ups | Intent routing, extracted title-page/margin context and bounded conversation history; no verified author catalog or author-search UI claim |
| Clickable sources | Citation resolver, `DocumentWorkspace`, `CitedAnswer` and the shared React-PDF panel |
| Offline Ragas | `evaluation/` optional Ragas 0.2.15 `EvaluationDataset` / `evaluate()` adapter, metrics and reviewed-source reports |
| Docker / CI | Existing Compose files, Dockerfiles, Nginx config, smoke script and GitHub Actions jobs |

Declared dependencies alone are not capability evidence. The active keyword search
uses Atlas BM25, not the declared Python `rank-bm25` package. Reserved cheap/vision
model roles and Voyage reranker settings do not implement automatic fallback,
vision processing or reranking. `OPENROUTER_BASE_URL` is not consumed; the actual
client already uses the fixed OpenRouter endpoint. Runtime prompts remain source
code and were not removed.

## Web guidance applied

Modern Web Guidance search and current retrieved accessibility, dialog and form
factor guides informed review of native dialog semantics, accessible names,
keyboard dismissal/focus return, status announcements, intrinsic sizing and
responsive overflow. Existing code and tests implement these behaviors; no new
framework, component rewrite or dependency was needed. No WCAG certification, screen-reader or physical-device
claim is made. Browser assertions and actual screenshots were inspected.

## Security review

Current tracked/proposed text and 871 unique text blobs across 105 reachable
commits and 61 local/remote refs were checked for provider-key/private-key
signatures, non-placeholder credentialed MongoDB URIs, and exact matches to local
configured credentials. Values were never emitted. **No matching credential was found**, and
`.env` is ignored and untracked. This is a bounded review, not a proof that every
possible secret format is absent: binary/large blobs, unreachable Git objects,
remote secret-scanning results and infrastructure authorization were not audited.
No history was rewritten. Credentials previously shared outside Git should still
be rotated in their providers and updated locally; this cleanup did not revoke or
remove working keys.

`npm audit --json --ignore-scripts` reported **10 affected package entries: three
critical, five high and two moderate**, including transitive dependencies. These
were pre-existing; no automatic audit fix or major-version upgrade was attempted.

- The production PDF.js dependency is affected by
  [GHSA-wgrm-67xf-hhpq](https://github.com/advisories/GHSA-wgrm-67xf-hhpq).
  Existing viewer options disable eval, which is a mitigation, not an upgrade or
  a clean audit result.
- Dev/build/test dependencies include Vite/esbuild, Vitest/tinypool and transitive
  tar/canvas paths. See [Vitest advisory](https://github.com/advisories/GHSA-5xrq-8626-4rwp)
  and [tinypool advisory](https://github.com/advisories/GHSA-5gmw-xhrv-c9v3).
  Audit severity does not mean every exploit path was reproduced in this app.
- A separate reviewed dependency upgrade with PDF/browser/build regression checks
  is required. Backend dependency vulnerability scanning and public deployment
  penetration testing were **NOT TESTED** in this cleanup.

Authentication, authorization and public TLS operation are absent. CORS and opaque
IDs are not access control. Do not expose this local/demo runtime publicly without
addressing those boundaries.

## Verification performed

Tests used an exact tracked-source copy plus these documentation changes; the
13 unrelated original edits/untracked files and local `.env` were excluded.
Dependencies were reused. A temporary Vite setting allowed the shared dependency
location for this copy and put caches outside the repository; no application
configuration change was introduced for testing.

| Check | Result / scope |
| --- | --- |
| Backend pytest, non-paid markers | **PASS — 486 passed, 4 paid checks deselected**, real disposable MongoDB/RabbitMQ; two upstream deprecation warnings |
| Python lint | **PASS** — `ruff check backend`, smoke-script lint and format check |
| Frontend Vitest | **PASS — 159 tests in 22 files**; unrelated untracked legacy tests excluded |
| TypeScript | **PASS** — application and browser-test configurations |
| Production build | **PASS** — existing PDF.js eval warning remains |
| Chromium deterministic browser suite | **PASS — 21 scenarios**, API fixtures and actual PDF.js rendering |
| Responsive widths | **PASS** — 375, 768, 1024, 1280, 1440, 1920px; no root overflow in covered cases |
| Frontend lint | **NOT CONFIGURED** — no standalone lint command; no invented ESLint result |
| Docker full-stack smoke | **PASS** — builds, health/non-root images, static/PDF assets, Nginx API proxy, upload/dedup/GridFS/status/delete; no provider keys |
| FastAPI startup | **PASS** — isolated real HTTP health and OpenAPI, 14 paths |
| Safe environment template | **PASS** — Settings validation, placeholder keys and intended ignore rules |
| Documentation links / diff | **PASS** for cleanup files; original unrelated whitespace warnings preserved |
| Full Ragas evaluation | **NOT RUN** — offline deterministic evaluation tests included above; existing measured reports retained |
| Fresh empty-machine native install | **NOT TESTED** — installed tools reused; Docker build/runtime verified |

### Isolated real-provider smoke

One page of the licensed public *Lost in the Middle* paper was processed with the
existing configured primary model `openai/gpt-5.6-luna`. Real LlamaParse, Voyage,
OpenRouter, GridFS and RabbitMQ were used with a separate Atlas-local search
container and fresh database/queues. The test bounded job attempts to one.
This was not a new cloud-Atlas deployment, full-paper test or accuracy benchmark.

- **PASS:** multipart upload, SHA-256 deduplication and original-byte download.
- **PASS:** actual Pending → Parsing → Summarizing → Ready lifecycle, published
  five-section summary, seven authors and seven validated summary source records.
- **PASS:** actual hybrid metadata question returned the seven authors and one
  document-scoped page-1 citation. Browser source resolution returned HTTP 200.
- **PASS:** actual Dashboard/upload dialog, real deduplicated browser upload,
  saved summary, restored generated chat history, hidden-by-default PDF, page-1
  citation navigation and mobile viewer with no horizontal overflow.
- **PASS:** chat/draft/page/125% zoom survived PDF toggles with zero extra PDF loads.
- **PASS:** no uncaught browser errors in these smoke interactions. Desktop and
  mobile screenshots were inspected. No additional model calls were used just to
  repeat UI assertions.
- **PASS:** deletion of this review's own paper returned 204; subsequent metadata/
  original reads returned 404, scoped records and GridFS files were zero. Owned
  processes and all three disposable containers were removed. User data and the
  normal runtime were not selected. Final normal gateway/frontend HTTP checks
  returned 200 and the original worker process remained running.

The private smoke harness initially sent extra citation-response fields to the
strict selection endpoint and used the wrong case for an exact zoom-button label.
Those harness assertions were corrected to the existing public contract/label;
no product code changed to make a test pass. Initial evidence was retained.

**NOT TESTED:** a fresh full 17-page paper workflow on the funded configuration,
current cloud-Atlas end-to-end retest, multiple generated citation pages in this
one-page smoke, physical mobile devices, Safari/Firefox and assistive technology.
Deterministic seven-page navigation/highlighting cases passed separately. Earlier
live full-paper quote/attribution failures and rapid-tab/instant-refresh issues
remain in [the live QA report](live-e2e-qa-2026-11-14.md); cleanup does not fix them.

## GitHub presentation and handoff

The public repository's description is currently empty. Suggested description:

> AI research paper assistant with structured PDF summaries, document-grounded
> question answering, hybrid retrieval, and clickable source citations.

The root README now answers the interview questions about the problem, storage,
pipeline, retrieval, citations, evaluation and setup without asserting unverified
production readiness. The current default-branch contents were inspected, but
remote CI for these uncommitted changes cannot exist yet. This review does not
change branch protection or publish images/artifacts.

### Files changed by this review

- `.env.example`
- `.gitignore`
- `README.md`
- `backend/gateway/README.md`
- `backend/services/document_processor/README.md`
- `backend/services/summary_service/README.md`
- `backend/shared/README.md`
- `docs/README.md`
- `docs/architecture.md`
- `docs/atlas-setup.md`
- `docs/atlas-verification.md`
- `docs/background-jobs.md`
- `docs/browser-qa.md`
- `docs/ci.md`
- `docs/deployment.md`
- `docs/development-roadmap.md`
- `docs/final-qa.md`
- `docs/hybrid-rag.md`
- `docs/markdown-chunking.md`
- `docs/pdf-citations.md`
- `docs/provider-configuration.md`
- `docs/rag-evaluation.md`
- `docs/screenshots.md`
- `docs/structured-summary.md`
- `docs/submission-review.md`
- `docs/verification-report.md`
- `evaluation/README.md`
- `frontend/README.md`

All other original local modifications are excluded from this list. Review these
changes before selecting files for a commit; avoid a blanket `git add .`.

Suggested commit message:

```text
docs: prepare ResearchAI repository for interview submission
```

No new commit or push was made. Remediate dependency advisories, review broader
model/source quality and independently approve the benchmark before calling the
repository fully ready for submission.
