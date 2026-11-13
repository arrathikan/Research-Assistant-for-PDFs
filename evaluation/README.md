# Offline RAG evaluation

Prompt 13 builds a reproducible evaluation workflow using the application's real
RAG retrieval/answer code and Ragas. Normal chat routes do not import evaluation.

The active benchmark is `datasets/rag_test_cases.json`: 20 source-grounded cases
from the CC-BY 4.0 published *Lost in the Middle* paper. It includes two unsupported
questions. Read [source/review provenance](datasets/README.md) and the
[source checklist](datasets/MANUAL_REVIEW.md). At the user's request, Codex checked
the references against the PDF; these are explicitly assistant reviews, not
human approval. Case hashes invalidate review records when content changes.

The original five-case `benchmark_dataset.json` is an unverified legacy scaffold
and is not used by the new runner. Real benchmark outputs and verification notes
are published under [reports](reports/README.md).

Use a separate environment to keep optional evaluation dependencies away from
running gateway/workers:

```bash
python3 -m venv .venv-evaluation
source .venv-evaluation/bin/activate
pip install -r backend/requirements.txt -r evaluation/requirements.txt
```

Ragas 0.2.15 is compatible with this project's LangChain 0.3 stack and supports
`EvaluationDataset` and `evaluate()`. Metric imports are verified against that
installed version. [Official API](https://docs.ragas.io/en/v0.2.15/references/evaluate/).

Local `results/` artifacts are ignored because they may contain paper/context
text. Publish only deliberately reviewed shareable reports under `reports/`.


Collection now uses the actual RAG answer composition and document-scoped Atlas
query/filter validation. A paired helper shares one query vector and candidate
snapshot between semantic and hybrid rankings. Semantic ignores keyword results;
hybrid uses the existing RRF. Retrieval duration is shared and is not a valid
per-strategy latency comparison. Answers are independent single turns and are
not inserted into user chat history. Failed retrieval/generation is recorded
without fabricated contexts or answers. PDF hash/page count and the current
source generation are checked before paid work and after generation.


The five implemented metrics are faithfulness, answer relevancy, reference-based
context precision, context recall and factual correctness (F1). Ragas 0.2.15
uses `EvaluationDataset` / `evaluate()` with explicit provider adapters. All judge
completions go through OpenRouter; relevancy embeddings use Voyage query vectors
for both original and generated questions. No default OpenAI provider is used.
Anonymous Ragas telemetry is disabled in the evaluation process.

`EVAL_*` settings in `.env.example` bound evaluator timeouts, concurrency, output
size, question count and request/input budgets. Failed/invalid/non-finite scores
remain null with a reason. Genuine zero scores are retained. Unsupported cases
use separate abstention/manual checks; reference-dependent metrics are skipped
when references are absent, and empty-context/abstention cases are explicitly
marked as inapplicable where necessary. Means must state their sample coverage.
Ragas is optional and is not installed as a required serving dependency.


## Run the workflow

From the repository root, use the separate evaluation environment described above.
The gateway/workers should first process the exact benchmark PDF. Create a local
bindings JSON mapping `lost-in-middle-tacl-2024` to its actual document ID.
Keep that file outside version control.

```bash
python -m evaluation.evaluate validate --pdf /absolute/path/to/2024.tacl-1.9.pdf
python -m evaluation.evaluate collect --bindings /absolute/path/to/bindings.json --limit 20 --live
python -m evaluation.evaluate score --collection evaluation/results/collection-RUN_ID.json --live
```

Or collect and score in one invocation:

```bash
python -m evaluation.evaluate run --bindings /absolute/path/to/bindings.json --limit 20 --live
```

Use `--sample-id lim_01` (repeatable), `--limit 2` for a small smoke run, or
`--strategy hybrid` / `--strategy semantic` to select output variants. Unreviewed
drafts require `--allow-unreviewed` and retain their missing review provenance.
The configured `EVAL_MAX_SAMPLES` and evaluator request budgets bound work.
Collections are saved before judging, so scoring can be retried without rerunning
paid answer generation. Every scoring run gets a new evaluation ID.

Generate a pending result-review template:

```bash
python -m evaluation.evaluate manual-template --collection evaluation/results/collection-RUN_ID.json --output /absolute/path/to/manual-review.json
```

Fill it only after actually reviewing the corresponding answers/evidence. Add
reviews to an existing scored report without provider calls:

```bash
python -m evaluation.evaluate review --report evaluation/results/evaluation-EVALUATION_ID.json --manual /absolute/path/to/manual-review.json
```

This creates a new evaluation ID linked to the original report, preserves measured
scores/request counts, and validates that each review matches the unchanged
result. Unknown sample/strategy keys are rejected. Alternatively, supply `--manual`
to `score` when scoring for the first time. To render an existing score artifact
without paid calls:

```bash
python -m evaluation.report evaluation/results/evaluation-EVALUATION_ID.json --output /absolute/path/to/new-report.md
```

Run deterministic evaluation tests separately from paid runs:

```bash
RAGAS_DO_NOT_TRACK=true python -m pytest backend/tests/test_benchmark_dataset.py backend/tests/test_evaluation_collection.py backend/tests/test_evaluation_metrics.py backend/tests/test_evaluation_judge.py backend/tests/test_evaluation_report.py -q
```

The installed-Ragas adapter check uses local HTTP fixtures. All numeric fixture
scores in unit tests are explicitly test data, never published benchmark results.
See [the methodology](../docs/rag-evaluation.md) for interpreting real scores.

## Research-assistant intent checks

Use the separate nine-case dataset and curated follow-up seed history:

```sh
RAGAS_DO_NOT_TRACK=true python -m evaluation.evaluate validate \
  --dataset evaluation/datasets/intent_test_cases.json --pdf /path/to/published-paper.pdf
RAGAS_DO_NOT_TRACK=true python -m evaluation.evaluate collect \
  --dataset evaluation/datasets/intent_test_cases.json \
  --history evaluation/datasets/intent_history.json \
  --bindings /private/path/to/document-bindings.json --limit 9 --live
```

Then score the saved collection using the existing score command. Both strategies
share section samples for an overview and no retrieval for general knowledge;
those rows compare generation behavior, not hybrid versus semantic ranking.
Facts retain the configured narrow limit; other paper queries use the bounded
broader context with section diversity for both strategies. Initial and corrected
runs retain their actual pipeline commit, prompt hash, source identity and
dataset hash.

General-only cases are evaluated for clear labeling and absence of paper
citations, not paper faithfulness. Mixed cases score paper faithfulness and
reference correctness on the paper portion and answer relevance on the complete
response. Ragas receives the literal current question for follow-ups; its
single-turn relevance metric may underrate context-dependent wording. Review
follow-ups with their recorded seed history and reference. Results do not
establish general accuracy, and no human review is implied by assistant checks.

## Final QA follow-up (2026-11-13)

The [latest nine-case paired run](reports/2026-11-13-final-qa/README.md) uses the
completed v2 saved summary. All 18 responses generated; Ragas recorded 58 real
metric values, 30 appropriate skips and two overview context-recall errors.
All outputs have assistant source reviews, including remaining citation and
attribution failures. This partial run is retained without substituting missing
values or claiming independent human approval or general hybrid superiority.
