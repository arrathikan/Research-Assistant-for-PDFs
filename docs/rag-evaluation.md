# RAG evaluation methodology

The evaluator measures the actual ResearchAI pipeline offline. Ragas never runs
inside a user chat request. The benchmark binds its document key to an uploaded
MongoDB document only after the original PDF SHA-256 and page count match.

## Dataset and review

The active dataset has 20 cases from the CC-BY 4.0 TACL paper *Lost in the Middle*.
It covers bibliographic facts, problem/methodology, datasets, experimental
settings, numerical results, conclusion, limitations and two unsupported questions.
See [source attribution](../evaluation/datasets/README.md) and the
[source review checklist](../evaluation/datasets/MANUAL_REVIEW.md).
Page references use 1-based PDF pages. The original five-case scaffold is unused.
The user delegated the source review to Codex; those records are marked assistant,
with case hashes and notes. No human review is claimed. Generated-answer reviews
are separate and are tied to hashes of the actual collected results.

## Real collection and fair comparison

Collection calls the production Atlas retrieval helpers and source-validated
answer chain, with isolated single-turn history and no writes to user chats.
Question, contexts, answer, citations, chunk IDs, source pages, answer latency and
pipeline settings are retained in private JSON. Collection failures preserve an
error state rather than creating fake contexts/answers.

Hybrid and semantic rankings share one query vector and source snapshot. Semantic
preserves vector ranking; hybrid uses the existing vector/BM25 RRF. Keyword
retrieval is still fetched for the paired comparison, so shared retrieval time
must not be presented as standalone semantic latency. The same candidate/context
limits, document generation and answer-model settings apply to both strategies.
Averages show their coverage; comparisons use only the same-case metric pairs.
Do not claim hybrid is superior without supporting measured results.

## Metrics and interpretation

- Faithfulness checks answer claims against retrieved evidence.
- Answer relevancy compares the question with questions generated from the answer.
- Context precision checks the relevance ordering of retrieved contexts against a reference.
- Context recall checks whether retrieved contexts cover the reference's claims.
- Factual correctness uses claim-level F1 between the answer and the reference.

Ragas 0.2.15 `EvaluationDataset` and `evaluate()` are used with the installed
metric classes. Evaluator calls explicitly use OpenRouter; relevancy uses Voyage
query embeddings for both sides. Defaults, model settings, concurrency and
request budgets are in `.env.example`. No implicit OpenAI calls or Ragas telemetry
are enabled. Ragas is an optional evaluation dependency.

Missing references skip reference-dependent metrics. Empty contexts and factual
abstentions are labeled inapplicable where necessary. Unsupported cases use
abstention/manual checks instead of misleading reference metrics. Errors, NaN,
infinity and invalid score shapes remain null with reasons; zero is retained as
a real score. Most metrics are 0–1; the raw relevancy cosine can range from -1 to 1.
No overall accuracy percentage is invented from these different metrics.

Reports include individual values, means/counts, skips/errors, paired deltas,
pipeline/evaluator configuration, Git/source/dataset identities, deterministic
citation checks and manual-review results. JSON summary values are validated
against the individual results. A run with technical metric failures is partial.
A completed execution does not mean the model answered every question correctly.

## Manual result checks

For selected actual outputs, check answer correctness, evidence support, citation
pages, source-text matching and unsupported-question handling. Record pass/fail,
not-applicable or pending, plus reviewer, provenance, timestamp and comments.
Do not replace these checks with a Ragas score. Page-coverage diagnostics are
coarse indicators, not Ragas context recall or proof of citation correctness.

## Commands and privacy

Follow the executable commands in [evaluation/README.md](../evaluation/README.md).
Normal CI runs deterministic tests with mocked providers; paid benchmark runs
need explicit `--live`. Rerunning collection/generation or judging consumes
provider credits. Request budgets are limits, not billing estimates.
Local results are ignored by Git and created without overwriting existing files.
Publish only reviewed, shareable runs; private-paper contexts and conversations
must stay out of version control.

LLM judges can vary, fail or share biases with the answer model. One paper and a
small dataset cannot establish general scientific-answer accuracy. Review errors,
qualifiers and low scores before making retrieval or prompting changes.

References: [Ragas API](https://docs.ragas.io/en/v0.2.15/references/evaluate/),
[metric definitions](https://docs.ragas.io/en/v0.2.15/references/metrics/),
[source paper](https://aclanthology.org/2024.tacl-1.9/).
