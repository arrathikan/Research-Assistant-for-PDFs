# Research-assistant intent evaluation — 2026-11-12

These are measured runs on the nine assistant-reviewed cases in
[the intent dataset](../../datasets/intent_test_cases.json), with
[reference/source checks](../../datasets/INTENT_REVIEW.md) and one explicitly
curated follow-up seed exchange. All use the same published CC-BY 4.0 paper,
*Lost in the Middle: How Language Models Use Long Contexts*, TACL 12 (2024),
[authors/source](https://aclanthology.org/2024.tacl-1.9/),
DOI 10.1162/tacl_a_00638. The source PDF is not committed. Source-derived excerpts
and adapted reference answers retain CC-BY 4.0 attribution.

## Runs and reproducibility

- [Initial v2 report](initial/evaluation-c160068167b34cab938021035d616fe2.md): commit `2a3c24e`, 18 attempts,
  7 generation failures and one false overview abstention. There are 32 actual
  metric values, 23 skips and 35 generation-error metric states. All 18 results
  have assistant reviews.
- [Intermediate v3 collection](intermediate/collection-4c1dadb4cba64e0e873b2be127006b05.json):
  commit `d50529a`, 18 attempts, 6 generation failures. This diagnostic
  collection was not Ragas-scored; no scores are invented for it.
- [Final v4 report](final/evaluation-e093ab7cb4c2409d9dc34d5dd98c9719.md) / [JSON](final/evaluation-e093ab7cb4c2409d9dc34d5dd98c9719.json):
  commit `ba5f019`, all 18 responses generated, including correct unsupported
  abstentions and separately labeled general explanations. **60 measured metric
  values, 30 appropriate skips, no metric errors.** There are 18 result-bound
  assistant reviews. General/unsupported cases have no fabricated paper scores.

Each artifact retains its actual code commit, dataset/source hashes, prompt hash,
source generation, context, model settings and provider usage. The final judging
used Ragas 0.2.15 with 257 actual LLM requests and 48 embedding inputs; collection
generation/retrieval requests are separate. It did not modify user chat history.
Follow the [offline commands](../../README.md#research-assistant-intent-checks).
The complete scoring status means the evaluator executed; it does not mean every
answer is correct.

## Final measured means and coverage

| Metric | Hybrid | Semantic | Scored cases |
|---|---:|---:|---:|
| faithfulness | 0.9132 | 0.9609 | 6 each |
| answer_relevancy | 0.5561 | 0.5765 | 6 each |
| context_precision | 0.9221 | 0.8371 | 6 each |
| context_recall | 0.8968 | 0.8968 | 6 each |
| factual_correctness | 0.5900 | 0.5950 | 6 each |

Three cases per strategy (unsupported gender topic, unreported GPU temperature,
general knowledge) use guardrail/labeling review rather than paper-reference
metrics. Mixed-answer faithfulness/correctness use the paper portion, while
relevance uses the entire answer. Overview context is shared section sampling,
so its pair does not measure ranking differences. The semantic strategy preserves
dense ranking before the same broad-context policy; hybrid uses the existing RRF.

The initial and final mean scores have different successful-case coverage and
must not be compared as an accuracy improvement. Final metrics also do not show
an overall hybrid advantage. Literal-question relevance can underrate a pronoun-
dependent follow-up; inspect the recorded seed history. Short reference answers,
one source paper, stochastic generation and a single judge model limit inference.
No overall accuracy percentage or statistical superiority is claimed.

## Manual findings and remaining quality work

All source identities, selected generations and canonical quotes passed their
server checks. Manual review nevertheless flags **five responses with incomplete
claim-to-citation support**:

- Both overviews include a true GPT-4 detail without its supporting page-16
  citation; multi-fact paragraphs can cite windows that establish only part of
  the statement.
- Hybrid analysis attaches page-6 evidence to the random-distractor finding and
  attributes an inferred access/weighting recommendation as the authors'
  conclusion. Its answer/attribution check fails as well.
- Semantic follow-up adds an 8K remark whose selected quotes omit the supporting
  sentence on page 8.
- Hybrid mixed answer cites random-order experimental setup rather than the
  result supporting that particular claim.

The other supported answers and guardrail cases were checked against the
references. Reviews are attributed to **Codex / assistant**, not human approval.
Ragas faithfulness checks whole retrieved context, not whether each inline
citation entails its attached claim; these manual findings remain essential.
General background is model knowledge, not verified external research.

The live source document already had a failed saved-summary job. Overviews
therefore exercised bounded section fallback, not a successful live cache read.
Complete current-summary reuse has deterministic and MongoDB integration
coverage. Section sampling (at most 20 chunks), simple English routing and a
bounded history window cannot guarantee exhaustive coverage of every paper.
PDF rendering may differ from extracted Markdown; highlights remain conditional
and quiet page navigation is the fallback.

## Functional verification

- Backend: **463 passed, 4 optional live checks skipped** using a disposable
  database and isolated real broker queues; provider boundaries simulated.
- Frontend: **99 passed** in the preserved workspace; **95 passed** in the
  isolated proposed frontend. Both production/type builds passed.
- Benchmark/report regression subset: **22 passed**. Scoped Ruff lint/format
  and source PDF/hash/page/anchor validation passed.
- Browser: Sources starts closed and opens on request; inline citation reached
  actual PDF page 3 with a real highlight and no technical fallback message.
  Chat checks at 375, 768, 1280 and 1440 pixels had no horizontal page overflow.
- Final server-built factual citations both resolved through the real HTTP API
  to current PDF page 3. One transient Atlas timeout recovered after reconnecting
  the owned local API; no backend API or storage configuration was changed.
- Existing PDF.js eval/bundle-size and upstream deprecation warnings remain.
