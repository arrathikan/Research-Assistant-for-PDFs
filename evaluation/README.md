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
and is not used by the new runner. No benchmark scores have been computed yet.

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
