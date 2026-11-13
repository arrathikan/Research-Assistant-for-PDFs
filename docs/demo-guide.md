# ResearchAI demo and interview guide

Use the [final QA report](final-qa.md) to distinguish working flows, measured
quality and remaining release work. This is a local/demo application.

## Prepare

1. Follow [deployment](deployment.md) and keep credentials in the ignored root
   `.env`. Atlas Network Access must permit the runtime's actual outgoing IP.
2. Start one runtime setup. For the full Docker application, use
   `docker compose up --build -d`, then `docker compose ps`; open
   `http://localhost:3000`. The native setup uses the gateway on 8000, workers
   and Vite on `http://localhost:5173`. Avoid port conflicts between setups.
3. Check gateway liveness and worker health. Liveness does not prove Atlas,
   provider credits or model readiness; use a real processing/job check too.
4. Obtain the reviewed public [Lost in the Middle paper](https://aclanthology.org/2024.tacl-1.9/).
   Use the exact 17-page publisher PDF for reproducible questions. Cite Liu et al.
   (2024), TACL, CC-BY-4.0 when showing paper excerpts.
5. Upload it ahead of the interview and wait for confirmed Ready. Leave time for
   parsing/model latency and provider retries. Keep a previously verified result
   available for a dependable demo; explain that it is cached.

The Dashboard library currently lasts for the browser's app session. After a full
reload, select/upload the same PDF again: SHA-256 deduplication reuses its stored
record and matching completed outputs. Chat history is document-scoped; the
conversation pointer is kept in session storage. Do not present this as account
sync or a persistent cross-device document library.

## Suggested six-minute walkthrough

| Time | Show | Explain |
|---|---|---|
| 0:00–0:40 | Dashboard and Upload Paper | ResearchAI organizes a PDF into a structured summary and a source-supported conversation. |
| 0:40–1:30 | Drag/select PDF, upload/status | Storage deduplicates by SHA-256. Real workers handle parsing, chunking, embeddings and summary. Reusing a Ready PDF skips those completed outputs. |
| 1:30–2:30 | Five summary sections | Title/authors/abstract, problem, methodology, key results, conclusion; missing information stays explicit. |
| 2:30–3:30 | Ask the precise question below | A natural-language answer is accompanied by paper-specific sources. |
| 3:30–4:30 | Click an inline citation | The same optional PDF viewer opens at the verified source page; text is highlighted when an accurate match exists. |
| 4:30–5:15 | Close/open PDF; resize mobile | Chat/draft and summary remain intact; mobile has a full-screen viewer and clear close action. |
| 5:15–6:00 | Unsupported question and evaluation | Show honest abstention and explain measured evaluation/citation limitations. |

Useful questions for this exact source:

- “How many NaturalQuestions queries were used in the multi-document QA setup,
  and what answer type was selected?” The reviewed answer is 2,655 paragraph long
  answers, excluding lists/tables, on PDF page 3 (printed page 159).
- “Compare query-aware contextualization for key-value retrieval and
  multi-document question answering.” Check the actual returned sources; the
  core contrast is on PDF pages 8–9.
- “What GPU temperature did the researchers maintain?” This paper does not report
  it; the benchmark correctly abstained.
- “In general, what is retrieval-augmented generation?” General background should
  be labeled separately from findings of this paper.

Show the citation pages actually returned; do not promise example page numbers
for another PDF. Expand Sources only when inspecting supporting passages. Use
zoom when the original paper's text is small. Missing exact text highlighting
uses a quiet page fallback. An invalid/stale source gets a friendly error.

If demonstrating paper actions, open the menu and cancel the delete dialog.
Use a disposable paper for any deliberate deletion demonstration.

## Explain the architecture

```text
PDF → FastAPI validation / SHA-256 → Atlas metadata + GridFS original
                                     ↓ durable outbox / RabbitMQ jobs
              LlamaParse → Markdown-aware chunks → Voyage embeddings
                                                   ↓
                           Atlas hybrid search + LangGraph summary
                                                   ↓
                            document-scoped chat → verified citations
                                                   ↓
                            optional React-PDF source viewer
```

Parsing preserves pages and source metadata. Chunking uses Markdown headings and
character overlap (the verified run used 1200/150, not token counts). Dense Atlas
search and lexical retrieval feed reciprocal rank fusion. The five-section
LangGraph workflow validates source quotes before publishing. Background jobs
own claims, retry bounded transient failures and preserve completed outputs.
The chatbot generates prose and the server constructs citations from selected
source passages; canonical identity/quote checks do not prove claim entailment.
Ragas runs offline and compares hybrid with semantic retrieval on shared cases.

## Interview talking points

- **Why asynchronous jobs?** Upload returns after safe storage; slow external
  parsing and model calls continue in separately running workers.
- **Why deduplication?** Identical bytes identify the same paper and prevent
  repeated storage/provider work when profiles are unchanged.
- **What did final QA find?** Model-elided source quotes caused summary failures.
  Short contiguous-quote guidance fixed the verified case while strict validation
  remained. The prompt version changes the summary profile hash.
- **How is accuracy checked?** Five appropriate Ragas metrics plus separate
  answer/source reviews. The latest 18-response run has 58 measured values,
  30 appropriate skips and two explicit metric errors. There is no universal
  accuracy percentage, and assistant review is not independent human approval.
- **What remains?** More complete claim-to-citation support, broader reviewed
  datasets, resolution of metric errors, dependency upgrades and production
  authentication/authorization/TLS. A passing browser suite is not scientific
  correctness or security certification.

## Recovery during a demo

- Upload error: check the gateway connection, PDF size/type and actual API result.
- Queued: confirm workers and RabbitMQ are running. Do not mark Ready manually.
- Failed: use Retry processing only when offered; it reuses valid completed
  stages. Interrupted jobs requiring review need the documented operator recovery.
- Chat/citation error: keep the existing answer, retry the question or open the
  original PDF. Atlas indexes/providers are separate from HTTP liveness.
- Unexpected slow response: acknowledge provider/Atlas latency and demonstrate
  an already completed result. Do not claim a cached result is newly generated.

See [browser QA](browser-qa.md) for reproducible checks and private screenshot
capture, [background jobs](background-jobs.md) for recovery, and
[the measured evaluation](../evaluation/reports/2026-11-13-final-qa/README.md) for
actual answers, sources, scores and failures.
