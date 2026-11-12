# Benchmark source and review provenance

The 20 cases use **Lost in the Middle: How Language Models Use Long Contexts**,
Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua,
Fabio Petroni and Percy Liang, TACL 12 (2024), pp. 157–173.
[Source](https://aclanthology.org/2024.tacl-1.9/),
[PDF](https://aclanthology.org/2024.tacl-1.9.pdf), DOI 10.1162/tacl_a_00638.
The PDF states © 2024 Association for Computational Linguistics, CC-BY 4.0.
Dataset answers are adapted/paraphrased; short evidence anchors retain source wording.
This source-derived dataset is provided with the same CC-BY 4.0 attribution.
The PDF itself is downloaded locally and is not committed.

Cases cover title/authors, problem, methodology, datasets, experiments, numerical
results, conclusion, limitations and two unsupported questions. Page references
are **1-based PDF pages**, not journal page numbers. The expected SHA-256 binds
the dataset to the 17-page published version. A logical document key is bound to
the actual MongoDB document ID at run time; no invented database IDs are stored.

At the user's request, Codex cross-checked all references against the actual PDF.
The table on PDF page 5 was visually inspected. The decoding-method case was
corrected to include the continuation on PDF page 5, alongside page 4. The review
records are explicitly **assistant** reviews. They do not assert human approval.
Independent human review is still useful and can replace a case's review with a
`human` record only when a person has actually performed it.

Review hashes bind decisions to unchanged case content. Changing a case makes
its old review invalid. The source-linked checklist is `MANUAL_REVIEW.md`.
The original five-case `evaluation/benchmark_dataset.json` is a legacy, unverified
scaffold and is not used by the new benchmark runner.


The separate intent_test_cases.json adds nine assistant-reviewed cases for the
research-chat refinement: overview, unsupported gender topic, exact count,
analysis, comparison, follow-up, missing measurement, general knowledge and a
mixed paper/background question. The same public source, license and exact PDF
identity apply. INTENT_REVIEW.md records reference checks; intent_history.json
contains one curated, source-checked seed exchange for the follow-up. That seed
is evaluation input, not a claim about a previous generated answer or a human
conversation. The original 20-case dataset and its result reviews are unchanged.
General knowledge has no paper reference; metrics requiring paper grounding are
inapplicable and labeling is reviewed separately.
