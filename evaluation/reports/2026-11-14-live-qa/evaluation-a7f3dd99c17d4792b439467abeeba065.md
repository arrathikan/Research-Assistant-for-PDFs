# ResearchAI offline RAG evaluation

Evaluation: `a7f3dd99c17d4792b439467abeeba065`
Date: 2026-11-13T15:04:37.033970+00:00
Execution status: **partial**
Dataset: lost-in-middle-20 / 1.0.0
Selected cases: 4 of 20; strategy records: 8.
Evaluated Git commit: `529c3947d74d5ff54879d9b6c50bbe8980f28475`
Reference review provenance: assistant.
Evaluator configuration: `{"completion_gateway": "OpenRouter", "judge_model": "meta-llama/llama-3.3-70b-instruct", "max_embedding_inputs": 60, "max_llm_requests": 160, "max_output_tokens": 2048, "max_samples": 4, "max_workers": 1, "metric_timeout_seconds": 180, "ragas_version": "0.2.15", "relevancy_embeddings": "Voyage query embeddings", "relevancy_questions": 3, "temperature": 0.1, "temperature_effective": 0.1, "timeout_seconds": 60}`
Request usage: `{"embedding_inputs": 0, "llm_requests": 0}`

Scores are computed metric outputs, not an overall accuracy percentage. Missing/failed values are never replaced with zero.
Unanswerable questions use abstention and manual checks rather than inappropriate reference-based metrics.
Retrieval time is shared between paired rankings; answer-chain latency excludes that shared retrieval time.

## Metric means and coverage

| Strategy | Metric | Mean | Scored | Skipped | Errors |
|---|---|---:|---:|---:|---:|
| hybrid | faithfulness | — | 0 | 0 | 4 |
| hybrid | answer_relevancy | — | 0 | 0 | 4 |
| hybrid | context_precision | — | 0 | 0 | 4 |
| hybrid | context_recall | — | 0 | 0 | 4 |
| hybrid | factual_correctness | — | 0 | 0 | 4 |
| semantic | faithfulness | — | 0 | 0 | 4 |
| semantic | answer_relevancy | — | 0 | 0 | 4 |
| semantic | context_precision | — | 0 | 0 | 4 |
| semantic | context_recall | — | 0 | 0 | 4 |
| semantic | factual_correctness | — | 0 | 0 | 4 |

## Paired comparison

Positive deltas favor hybrid for these measured pairs only. No general superiority claim follows from a small or incomplete benchmark.

| Metric | Paired cases | Mean hybrid − semantic |
|---|---:|---:|
| faithfulness | 0 | — |
| answer_relevancy | 0 | — |
| context_precision | 0 | — |
| context_recall | 0 | — |
| factual_correctness | 0 | — |

## Individual results and review

### lim_02 / hybrid

Question: Who are the authors of the paper?
Reference: Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual result review: pending.

### lim_02 / semantic

Question: Who are the authors of the paper?
Reference: Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual result review: pending.

### lim_05 / hybrid

Question: Where in a long context is relevant information generally used best and worst?
Reference: Performance is generally best near the beginning or end and worse in the middle.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual result review: pending.

### lim_05 / semantic

Question: Where in a long context is relevant information generally used best and worst?
Reference: Performance is generally best near the beginning or end and worse in the middle.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual result review: pending.

### lim_07 / hybrid

Question: How many queries are selected for the controlled multi-document QA experiments?
Reference: 2,655 queries whose annotated long answer is a paragraph.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual result review: pending.

### lim_07 / semantic

Question: How many queries are selected for the controlled multi-document QA experiments?
Reference: 2,655 queries whose annotated long answer is a paragraph.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual result review: pending.

### lim_19 / hybrid

Question: What vision-backbone training schedule does this paper prescribe?
Reference: Not applicable: unsupported question; expected abstention.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual result review: pending.

### lim_19 / semantic

Question: What vision-backbone training schedule does this paper prescribe?
Reference: Not applicable: unsupported question; expected abstention.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual result review: pending.

## Limitations

This is one paper and one model/pipeline configuration. LLM judges can vary or be wrong. Page coverage is a coarse deterministic diagnostic, not Ragas context recall. Reference approval and generated-answer review are separate. Assistant reviews are not independent human validation. See the JSON artifact for complete contexts and citations; do not publish private-paper runs.
