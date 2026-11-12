# Benchmark manual review

Approved source cases: 9/9.
Review provenance is explicit: assistant review is source cross-checking by Codex; independent human review is recorded only when supplied.
Review each answer against the linked PDF pages; check unsupported cases against the paper's scope.
Approval records must include reviewer, timestamp, decision, notes and the unchanged case hash.

## assistant-summary: summary

Question: Summarize this research paper, including its objective, methodology, main findings, conclusion and documented limitations.
Reference: The paper studies whether language models robustly use long contexts. It varies the location of relevant information and context length in multi-document question answering and synthetic UUID key-value retrieval. Performance often drops for information in the middle, even for explicitly long-context models. Extended context windows alone do not guarantee better use of context. Query-aware contextualization helps synthetic key-value retrieval much more than multi-document QA. The authors conclude that long-context evaluations must account for information position. These are controlled task/model results, not evidence about every research domain or current model.
Case hash: `ecb0d84215b4923108245a05ee8fde4834c3407644bf3d83ce44a077add5449d`

- [PDF page 1, Abstract](https://aclanthology.org/2024.tacl-1.9.pdf#page=1): We analyze the performance of language models on two tasks that require identifying relevant information in their input contexts: multi-document question answering and key-value retrieval.
- [PDF page 3, 2.1 Experimental Setup](https://aclanthology.org/2024.tacl-1.9.pdf#page=3): In particular, we take the 2655 queries where the annotated long answer is a paragraph (as opposed to a list or a table).
- [PDF page 6, 2.3 Results and Discussion](https://aclanthology.org/2024.tacl-1.9.pdf#page=6): Extended-context models are not necessarily better at using input context.
- [PDF page 8, 4.2 Effect of Query-Aware Contextualization](https://aclanthology.org/2024.tacl-1.9.pdf#page=8): We find that query-aware contextualization dramatically improves performance on the key-value retrieval task
- [PDF page 8, 4.2 Effect of Query-Aware Contextualization](https://aclanthology.org/2024.tacl-1.9.pdf#page=8): query-aware contextualization minimally affects performance trends in the multi-document question answering task
- [PDF page 11, 7 Conclusion](https://aclanthology.org/2024.tacl-1.9.pdf#page=11): performance is often lowest when models must use information in the middle of long input contexts.
Reviewer note: Overview references source experiment scope; the final qualification does not assert an undocumented dedicated limitations section.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Assistant source cross-check against the exact published 17-page PDF, including experiment qualifications and cited pages. Overview references source experiment scope; the final qualification does not assert an undocumented dedicated limitations section.

## assistant-gender: topic

Question: What does this paper say about gender differences, gender roles, or gender-related findings?
Reference: Outside the paper: follow the case-specific review note (unsupported paper facts require abstention; general knowledge requires a separate label).
Case hash: `21bdcdb35e3a65bce7e0eddfdb63f59472bbe32b097c195203608e5e34a4b9fb`

Reviewer note: Whole-paper scope and gender/sex synonyms checked; this paper investigates language-model context use, not demographic research. Expected clear insufficiency, no invented findings.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Assistant source cross-check against the exact published 17-page PDF, including experiment qualifications and cited pages. Whole-paper scope and gender/sex synonyms checked; this paper investigates language-model context use, not demographic research. Expected clear insufficiency, no invented findings.

## assistant-fact: fact

Question: How many NaturalQuestions-Open queries did the researchers select in Section 2.1?
Reference: They selected 2,655 queries whose annotated long answer was a paragraph rather than a list or table.
Case hash: `29381844f97166c2f1a0d4d483581516e26b5f061ecb7a65f602b8531494c84b`

- [PDF page 3, 2.1 Experimental Setup](https://aclanthology.org/2024.tacl-1.9.pdf#page=3): In particular, we take the 2655 queries where the annotated long answer is a paragraph (as opposed to a list or a table).
Reviewer note: Specifically Section 2.1, avoiding the distinct 500-example appendix subset.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Assistant source cross-check against the exact published 17-page PDF, including experiment qualifications and cited pages. Specifically Section 2.1, avoiding the distinct 500-example appendix subset.

## assistant-analysis: analysis

Question: Why does this paper conclude that a larger context window alone is not enough?
Reference: Models often struggle to use relevant information in the middle. When the same input fits both base and extended-context counterparts, performance is nearly identical. Thus capacity to accept more tokens does not itself establish robust access to their contents; this explanation follows the reported results rather than establishing a universal causal mechanism.
Case hash: `73e0b2ac32b8f1e23da1d7859d101eae47a2f6a0ef00124a77ecd04ba8c18333`

- [PDF page 6, 2.3 Results and Discussion](https://aclanthology.org/2024.tacl-1.9.pdf#page=6): Extended-context models are not necessarily better at using input context.
- [PDF page 6, 2.3 Results and Discussion](https://aclanthology.org/2024.tacl-1.9.pdf#page=6): performance between them is nearly identical.
- [PDF page 11, 7 Conclusion](https://aclanthology.org/2024.tacl-1.9.pdf#page=11): performance is often lowest when models must use information in the middle of long input contexts.
Reviewer note:

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Assistant source cross-check against the exact published 17-page PDF, including experiment qualifications and cited pages.

## assistant-comparison: comparison

Question: Compare the paper’s query-aware contextualization findings for key-value retrieval and multi-document question answering.
Reference: Query-aware contextualization places the query before and after the data. It dramatically improves synthetic key-value retrieval, reaching near-perfect performance across tested settings, but minimally changes multi-document QA trends: slightly better at the beginning and slightly worse in other settings.
Case hash: `3c7a5fbbfb7d74c49c30e2cd1e380dc24f8a6e9c9e61286f00b0063232d7bb23`

- [PDF page 8, 4.2 Effect of Query-Aware Contextualization](https://aclanthology.org/2024.tacl-1.9.pdf#page=8): We find that query-aware contextualization dramatically improves performance on the key-value retrieval task
- [PDF page 8, 4.2 Effect of Query-Aware Contextualization](https://aclanthology.org/2024.tacl-1.9.pdf#page=8): query-aware contextualization minimally affects performance trends in the multi-document question answering task
Reviewer note:

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Assistant source cross-check against the exact published 17-page PDF, including experiment qualifications and cited pages.

## assistant-followup: followup

Question: What happens beyond that length?
Reference: Beyond the encoder training-time context length, performance becomes more sensitive to information position: Flan-UL2 degrades for relevant information in the middle above 2,048 tokens, and Flan-T5-XXL shows a similar trend.
Case hash: `1edfa6f0d99e21bcb060092ec446601e88e51b6bf3f571152c13feb33b54298c`

- [PDF page 8, 4.1 Model Architecture](https://aclanthology.org/2024.tacl-1.9.pdf#page=8): When evaluated on settings with sequences longer than 2048 tokens
Reviewer note: Use the explicit source-checked seed exchange from intent_history.json; do not claim it was generated by a live prior turn.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Assistant source cross-check against the exact published 17-page PDF, including experiment qualifications and cited pages. Use the explicit source-checked seed exchange from intent_history.json; do not claim it was generated by a live prior turn.

## assistant-missing: unanswerable

Question: What GPU temperature did the researchers maintain during the experiments?
Reference: Outside the paper: follow the case-specific review note (unsupported paper facts require abstention; general knowledge requires a separate label).
Case hash: `aed9247ca54c9e9d2e6c626f3c713de2c24acfdebb845eafd31b5e5b03f66920`

Reviewer note: No GPU-temperature measurement or control is reported; whole-paper temperature search and experiment scope checked.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Assistant source cross-check against the exact published 17-page PDF, including experiment qualifications and cited pages. No GPU-temperature measurement or control is reported; whole-paper temperature search and experiment scope checked.

## assistant-general: general

Question: In general, what is retrieval-augmented generation (RAG)?
Reference: Outside the paper: follow the case-specific review note (unsupported paper facts require abstention; general knowledge requires a separate label).
Case hash: `e6ef8a7edffb856051cd495bfca9e0a06a8bd338bd33295434dd6f4185f3a905`

Reviewer note: General knowledge is outside this paper. Expected a labeled explanation from model knowledge with no paper citations. No fabricated paper reference or paper-faithfulness score.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Assistant source cross-check against the exact published 17-page PDF, including experiment qualifications and cited pages. General knowledge is outside this paper. Expected a labeled explanation from model knowledge with no paper citations. No fabricated paper reference or paper-faithfulness score.

## assistant-mixed: mixed

Question: Explain this paper’s middle-position finding, then give a general explanation of primacy bias.
Reference: The paper finds that language-model performance often degrades when relevant information is in the middle of long contexts, compared with the beginning or end. Its authors describe the beginning advantage as primacy bias. Any broader background explanation must be labeled separately and must not be presented as an additional finding of the uploaded paper.
Case hash: `8c1d812dd566a06ff5645ff3b9e5bdb38985123402eb9364bd14e1d45417de69`

- [PDF page 11, 7 Conclusion](https://aclanthology.org/2024.tacl-1.9.pdf#page=11): performance is often lowest when models must use information in the middle of long input contexts.
- [PDF page 6, 2.3 Results and Discussion](https://aclanthology.org/2024.tacl-1.9.pdf#page=6): the very beginning (primacy bias)
Reviewer note: Ragas grounding/correctness apply only to the paper portion; manual review separately checks general-background labeling.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Assistant source cross-check against the exact published 17-page PDF, including experiment qualifications and cited pages. Ragas grounding/correctness apply only to the paper portion; manual review separately checks general-background labeling.
