# Live QA evaluation — 13–14 November 2026

This directory records actual offline Ragas executions against the public *Lost in the Middle* paper. It is not a passing release benchmark.

- [Measured baseline and eight assistant reviews](evaluation-2f9d3478e36941e0ac97be072f036640.md) ([complete JSON](evaluation-2f9d3478e36941e0ac97be072f036640.json)). Four questions × hybrid/semantic; 20 numeric metrics, 20 appropriate skips, no metric errors. Each strategy/metric mean has only two scored cases.
- [Blocked post-change retest](evaluation-a7f3dd99c17d4792b439467abeeba065.md) ([complete JSON](evaluation-a7f3dd99c17d4792b439467abeeba065.json)). All eight generations failed; all 40 metric cells explicitly record errors. No judge or relevancy-embedding requests were made for this failed collection. These errors are not numeric zero scores.
- [Application QA and remaining failures](../../../docs/live-e2e-qa-2026-11-14.md).

The baseline used Ragas 0.2.15, OpenRouter `meta-llama/llama-3.3-70b-instruct` as judge, temperature 0.1, one worker, and Voyage query embeddings. It consumed 64 judge requests and 16 embedding inputs. Revisions adding the eight result-hash-bound assistant reviews made zero provider requests. Assistant review is not independent human approval.

| Metric | Hybrid mean | Semantic mean | Scored cases per strategy |
|---|---:|---:|---:|
| Faithfulness | 1.0000 | 1.0000 | 2 |
| Answer relevancy | 0.9134 | 0.9290 | 2 |
| Context precision | 0.2083 | 0.5000 | 2 |
| Context recall | 1.0000 | 0.5000 | 2 |
| Factual correctness | 0.8350 | 0.5000 | 2 |

Manual review flags both `lim_05` answers: a paper question was routed to general background and given no paper evidence. It also flags semantic `lim_07`: 500 questions from an appendix experiment was substituted for the main experiment's 2,655 queries. Exact quotes and valid pages alone do not establish claim relevance. This small, single-paper sample does not establish overall accuracy or hybrid superiority.

Both collections record HEAD `529c3947d74d5ff54879d9b6c50bbe8980f28475`; they ran with uncommitted working-tree changes, not a pristine checkout. The private source snapshots and collection configurations distinguish before/after; do not treat these artifacts as proof that the final patch improved scores. Generation after the intent/chunking changes was blocked by OpenRouter HTTP 402. The account balance was exhausted at the time of these runs; exact billing details remain private. No further generation was requested after the user chose to finish blocked.

Source attribution: Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni and Percy Liang, *Lost in the Middle: How Language Models Use Long Contexts*, TACL 12 (2024), 157–173, DOI [10.1162/tacl_a_00638](https://doi.org/10.1162/tacl_a_00638), [ACL Anthology](https://aclanthology.org/2024.tacl-1.9/), CC BY 4.0. JSON contexts contain this public source and public benchmark questions only. No PDF binaries, keys or private user research are included.
