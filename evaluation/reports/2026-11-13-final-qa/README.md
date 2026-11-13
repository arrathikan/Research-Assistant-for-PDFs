# Final QA Ragas follow-up — 2026-11-13

This is a measured follow-up on the same nine assistant-reviewed intent cases as
[the earlier run](../2026-11-12-assistant/README.md). It uses the real configured
pipeline at commit `146aed66415b6b428ff07c51cda6db6cb27c2055`, including the newly
completed `grounded-summary-v2` summary. It is not a new accuracy guarantee.

[Full report](evaluation-e03061c486b34739818cdbfe14689146.md) · [Structured results and traces](evaluation-e03061c486b34739818cdbfe14689146.json)

## Provenance and scope

Source: Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua,
Fabio Petroni and Percy Liang (2024), *Lost in the Middle: How Language Models Use
Long Contexts*, TACL 12, DOI 10.1162/tacl_a_00638.
[Publisher/source](https://aclanthology.org/2024.tacl-1.9/),
[public PDF](https://aclanthology.org/2024.tacl-1.9.pdf), **CC-BY-4.0**. Source-derived
excerpts and adapted reference answers retain this attribution/license. The PDF
itself is not committed. No private user papers or application conversations are
included. The seed follow-up is the explicitly curated benchmark history.

Source SHA-256: `f37f6fabe0fe0d8c73b67579cd115dbf14e282cfb7b7af655ae8109638402c9b`;
17 pages, 105 current chunks, 1200-character chunk size and 150-character overlap.
Generation uses `openai/gpt-5.6-luna`, Voyage `voyage-4-lite`/1024 dimensions and the
existing RAG v4 prompt. Context limits, prompt/source hashes, selected chunks,
quotes, pages, timing and complete answers are in the structured artifact.
Both overview traces explicitly record `summary_reused=true` and
`context_strategy=saved_summary`; earlier runs used section fallback because the
saved summary had failed. This change in context and stochastic generation makes
direct before/after mean-score improvement claims inappropriate.

## Actual execution

- 9 cases × 2 strategies = **18 real responses**, no generation failures.
- Ragas **0.2.15**, configured judge `meta-llama/llama-3.3-70b-instruct`.
- **58 measured metric values, 30 appropriate skips, 2 metric errors**.
- Scoring used **278 actual LLM requests and 48 embedding inputs**; collection
  generation/retrieval calls are additional. Caps were 350 requests/80 inputs.
- Both overview `context_recall` results were invalid/missing. They remain errors
  with null values. No zero, guessed result, or successful-case substitution was
  used. The report's execution status is **partial**.
- All 18 results have hash-bound systematic reviews attributed to **Codex /
  assistant**. Independent human sign-off is not claimed.

| Metric | Hybrid mean | Semantic mean | Scored per strategy |
|---|---:|---:|---:|
| Faithfulness | 0.9658 | 0.9465 | 6 |
| Answer relevancy | 0.6161 | 0.5451 | 6 |
| Context precision | 0.9641 | 0.8433 | 6 |
| Context recall | 0.9333 | 0.9333 | 5; 1 error |
| Factual correctness | 0.6167 | 0.5717 | 6 |

Unsupported gender/GPU questions and general RAG background use guardrail/manual
checks, not inappropriate paper-reference metrics. Mixed-answer reference metrics
score the paper-supported portion. Overview contexts are shared summary-based
sampling, so that pair does not measure a ranking difference. Other pairs share
the query/candidate snapshot before the existing context policy. One source,
small samples, a single judge and two missing values do not establish general
hybrid superiority or an overall accuracy percentage.

## Source-review findings

All canonical citation identities/pages and extraction quotes passed deterministic
checks. **Seven answers still have incomplete claim-to-citation support**:

- Both overviews attach incomplete citations to multi-fact methodology passages;
  hybrid cites pages 6–7 for a page-8 query-aware result, and semantic adds a true
  GPT-4 detail without its page-16 source.
- Both analysis answers turn tentative explanation into stronger author
  interpretation/prescription; semantic's encoder explanation lacks its page-8
  source. The core positional/window-size findings remain useful.
- Hybrid comparison reports the task-difficulty explanation as the paper's
  attribution, while its quotes establish task definitions/results. A later
  interpretation label does not fully resolve this wording.
- Hybrid mixed output cites QA passages for a two-task assertion. Semantic mixed
  output states the true 56.1% value but omits the page-6 quantitative citation.

The two analysis answers and hybrid comparison also fail the review's
answer/attribution criterion. Correct abstentions, general-background separation,
exact query count, semantic comparison and seed-based follow-ups were checked
separately. See each row's notes; a valid source quote does not guarantee that the
attached claim follows from it. Ragas faithfulness considers retrieved context,
so high faithfulness can coexist with these citation defects.

The saved UI summary itself includes broad multi-fact key results whose selected
quotes do not individually establish every detail (including GPT-4). Quote
validation establishes provenance, not complete scientific entailment. No
retrieval redesign or claim of solving this quality issue is part of final QA.

## Reproduce

Use the offline [intent-check commands](../../README.md#research-assistant-intent-checks)
with the exact public source, current document binding and the committed curated
history. This can consume provider credits; it never runs inside normal chat/CI.
The run was invoked with `EVAL_MAX_LLM_REQUESTS=350`,
`EVAL_MAX_EMBEDDING_INPUTS=80` and `--limit 9`. Attaching the assistant reviews used
the offline `review` command and made no new provider calls. A repeat can differ;
retain its own artifacts and error states rather than overwriting this run.
