# Versioned evaluation reports

[2026-11-12: Lost in the Middle, hybrid versus semantic](2026-11-12/README.md)
is the first measured public-paper baseline. It includes real failures and
assistant reviews. Read its coverage and limitations before using metric means.

Generated files use an evaluation UUID inside a dated directory. Each reviewed
JSON contains the original collection, source/dataset/Git identities, contexts,
answers, citations, pipeline/evaluator settings, individual metric states, paired
comparisons and result-bound review records. Its Markdown companion summarizes
the same values. Five metrics are retained: faithfulness, answer relevancy,
context precision, context recall and factual correctness.

Only deliberately reviewed, shareable artifacts belong here. Local private-paper
runs remain in ignored `evaluation/results/`. Never publish credentials, private
PDFs or user conversations.
