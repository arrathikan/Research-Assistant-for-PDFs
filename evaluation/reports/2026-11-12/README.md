# 2026-11-12 — First measured RAG baseline

This run used the actual Atlas retrieval, Voyage vectors and ResearchAI answer chain. Ragas values below came from paid provider executions. The baseline exposes quality and availability problems that remain to be improved.

- Collection: `92b5645893474674a3bbd3af9fef0e3f`; created 2026-11-12T07:26:15.059818+00:00.
- Reviewed evaluation: `b0df21fb688044af9bd2fa6b35aadbd9`; created 2026-11-12T07:37:02.253736+00:00.
- Evaluated code commit: `142f592ab40598dc170c4ec58c34832c8b517630`.
- Dataset: `lost-in-middle-20` / `1.0.0`; 20 questions, 18 answerable and 2 unsupported.
- Strategies: hybrid RRF and semantic-only, with 40 real attempts in total.
- Execution status: **partial**. Every metric retains an explicit score, skip or error state.
- Source-reference checks: 20 assistant reviews. Generated-result checks: 40 assistant reviews, with reviewer Codex and result hashes. **No independent human validation is claimed.**
- Provider usage for this scoring run: `{"embedding_inputs": 100, "llm_requests": 414}`. These counts exclude ingestion, answer collection, the earlier smoke run and a separate diagnostic.

[Full Markdown report](evaluation-b0df21fb688044af9bd2fa6b35aadbd9.md) · [Complete JSON evidence](evaluation-b0df21fb688044af9bd2fa6b35aadbd9.json) · [Installed package versions](environment.txt)

## Metric means and coverage

| Strategy | Metric | Mean | Scored | Skipped | Errors |
|---|---|---:|---:|---:|---:|
| hybrid | faithfulness | 0.9722 | 12 | 3 | 5 |
| hybrid | answer_relevancy | 0.7443 | 12 | 3 | 5 |
| hybrid | context_precision | 0.5572 | 13 | 2 | 5 |
| hybrid | context_recall | 0.9231 | 13 | 2 | 5 |
| hybrid | factual_correctness | 0.6600 | 12 | 3 | 5 |
| semantic | faithfulness | 1.0000 | 13 | 3 | 4 |
| semantic | answer_relevancy | 0.8250 | 13 | 3 | 4 |
| semantic | context_precision | 0.6208 | 14 | 2 | 4 |
| semantic | context_recall | 0.7857 | 14 | 2 | 4 |
| semantic | factual_correctness | 0.4977 | 13 | 3 | 4 |

Missing/error values are excluded from means and are never imputed as zero. Unsupported cases use separate abstention checks; answerable abstentions skip metrics requiring a factual answer. Paired deltas in the full report use only matching cases with valid values for both strategies. This single paper does not establish a general hybrid-search advantage.

## Reviewed failures and limitations

1. **9 generation failures:** {'generation_failed': 9}. No answer was saved for those attempts. Their five metric states are errors. The current collector does not retain retrieved contexts when generation fails, so those failed attempts cannot receive separate retrieval scores from this artifact. Retaining those intermediate traces is a follow-up improvement.
2. **2 false abstentions:** hybrid `lim_06` missed the NaturalQuestions-Open dataset; semantic `lim_14` missed the key-value setting counts. The source supports the answers on PDF pages 3 and 7 respectively.
3. **Two incorrect/incomplete semantic answers:** `lim_07` returned the appendix GPT-4 sample size of 500 instead of the main experiment’s 2,655 queries; `lim_11` returned only the appendix’s 20-document setting instead of the main 10/20/30 settings. PDF page 16 was visually checked against pages 3 and 5. Both answers have real, matching quotes, but those quotes do not establish the intended main-experiment answer. Deterministic quote validation alone does not ensure correctness.
4. **Unsupported questions:** 4/4 strategy attempts correctly abstained without citations. Two unsupported questions remain a small guardrail sample.
5. **Minor answer qualifiers:** semantic UUID-task wording omits the 128-bit detail; the query-aware example abbreviates GPT-3.5-Turbo (16K). Review notes retain these details rather than equating a passed broad answer check with perfect completeness.
6. **Separate diagnostic:** one additional `lim_03` generation, outside this scored baseline, reproduced citation rejection because the model inserted ellipses into quotes. The existing validator correctly rejected the altered source text. This identifies one failure mode; the other generation failures have only the recorded generic failure code.
7. **Source processing:** parsing, 105 Markdown chunks and Voyage embeddings completed for the exact public PDF. The separate summary background job ended with `SUMMARY_FAILED`; this benchmark measures the chatbot, and does not verify summary quality.
8. **Runtime and sampling:** Atlas connections initially exceeded the local 5-second timeout. The ignored local configuration was raised to 15 seconds and owned workers/gateway restarted before the successful collection. No credentials were changed. Results use one paper, one configuration and single-turn questions. Some main-versus-appendix questions could name their intended section more explicitly in a future dataset revision.

## Ragas cross-check disagreements

Systematic source checks are needed to interpret these scores. For `lim_07`, both
strategies received faithfulness 1.0, although semantic used the wrong experiment
size. The correct hybrid count, 2,655, received factual correctness 0.0; the
reference also mentions the paragraph-answer subset, which the short answer omits.
The source supports the count. These measured scores are retained unchanged;
manual review does not relabel or repair the automated values.

For semantic `lim_11`, Ragas context recall is 1.0 even though the intended main
Section 2.3 passage was not retrieved. A retrieved open-domain-QA table contains
10/20/30 among a larger sequence of document counts from a different experiment.
The manually reviewed answer still omits the main 10/20/30 setting. Hybrid
`lim_13` received faithfulness 0.6667 despite source passages supporting the UUID,
128-bit and retrieval-task statements. These are judge disagreements to calibrate,
rather than proof that any one metric is an accuracy oracle.

Across all returned citations, 34 of 36 snippets matched normalized extracted
PDF text; the remaining two were the figure labels visually verified on PDF
page 16. All 36 exist in the PDF, including the two used for the wrong experiment
scope. Full quote existence and factual answer correctness remain separate checks.

## Follow-up candidates

Preserve retrieval snapshots and more specific safe failure codes for unsuccessful generations. Ask the generator for short contiguous quotes without ellipses while retaining the strict source validator. Investigate main/appendix relevance ranking and evidence completeness. Make section scope explicit when revising ambiguous benchmark questions. Verify the separate summary failure. These improvements are proposed; this baseline does not claim they are implemented or effective. Version the dataset/pipeline and rerun the paired benchmark to measure any benefit.

## Verification and reproduction

- Final backend regression: **410 passed, 4 optional live checks skipped**, using disposable MongoDB and isolated queues on real local RabbitMQ. No serving data was deleted.
- The evaluation package and changed test/retrieval/provider files pass Ruff lint and formatting checks. Existing unrelated frontend edits were preserved.
- A preliminary one-question live smoke run computed all five Ragas metrics for each strategy. Its results are separate from the full baseline above.
- The `review` command attached actual result checks without further provider calls. Reviewed scores, collection and request counts match the original scored artifact.
- Use the commands in [the evaluation guide](../../README.md), the exact source PDF hash, dataset version, source generation and model settings recorded in JSON, and package versions in `environment.txt`. New LLM runs can differ despite matching configuration.

## Source and redistribution

*Lost in the Middle: How Language Models Use Long Contexts*, Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni and Percy Liang (2024), Transactions of the Association for Computational Linguistics. [Original publication and PDF](https://aclanthology.org/2024.tacl-1.9/). Copyright © 2024 Association for Computational Linguistics; distributed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The JSON contains LlamaParse-derived source excerpts whose formatting differs from the original PDF, plus generated answers and evaluation/review records. Only this published, shareable source is included. The uploaded PDF, credentials and private user conversations are excluded.
