# Benchmark manual review

Approved source cases: 20/20.
Review provenance is explicit: assistant review is source cross-checking by Codex; independent human review is recorded only when supplied.
Review each answer against the linked PDF pages; check unsupported cases against the paper's scope.
Approval records must include reviewer, timestamp, decision, notes and the unchanged case hash.

## lim_01: title

Question: What is the title of the paper?
Reference: Lost in the Middle: How Language Models Use Long Contexts.
Case hash: `1a882d23877e25c9e06eb9f1a876ec7cfebc8baf57cf383aecdfc64a33e02308`

- [PDF page 1, Title](https://aclanthology.org/2024.tacl-1.9.pdf#page=1): Lost in the Middle: How Language Models Use Long Contexts
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Title checked against the first-page heading.

## lim_02: authors

Question: Who are the authors of the paper?
Reference: Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang.
Case hash: `4dbb052d158c10f80f3b4adef0766b83c39b03b0bb8bcaaf11aa6a78a48bb403`

- [PDF page 1, Author block](https://aclanthology.org/2024.tacl-1.9.pdf#page=1): Nelson F. Liu
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: All seven authors checked against the title-page author block; affiliations excluded.

## lim_03: problem

Question: What uncertainty about long-context language models does the paper investigate?
Reference: Whether language models can reliably find and use relevant information throughout a long input context.
Case hash: `83b69ae21f959a36e4e57dbc494494ebe09a8a681b01dd97c8aa60f3f69f45c8`

- [PDF page 1, Introduction](https://aclanthology.org/2024.tacl-1.9.pdf#page=1): make use of their input contexts
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Introduction uncertainty about using extended contexts checked; no claim of universal model failure added.

## lim_04: tasks

Question: Which two tasks are used to study long-context information use?
Reference: Multi-document question answering and synthetic key-value retrieval.
Case hash: `9a36fc2dea4acef2abb1af9075776417767308de02850a8fbb40a3fef91d9036`

- [PDF page 1, Abstract](https://aclanthology.org/2024.tacl-1.9.pdf#page=1): key-value retrieval
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Both named tasks checked against the abstract.

## lim_05: results

Question: Where in a long context is relevant information generally used best and worst?
Reference: Performance is generally best near the beginning or end and worse in the middle.
Case hash: `6fd966d12c445440548cf7fbf5319f65250a3356f93296ec0548601b294f27f6`

- [PDF page 2, Figure 1](https://aclanthology.org/2024.tacl-1.9.pdf#page=2): U-shaped performance curve
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Figure 1 caption checked for primacy/recency and middle degradation; reference keeps the generally/often qualifier.

## lim_06: dataset

Question: Which question-answering dataset is used for the controlled multi-document QA task?
Reference: NaturalQuestions-Open, using questions with paragraph long answers.
Case hash: `24529d95cf19059f5d9023ae94658e1c9c45ca5eaf1f08a54f63edc41adafc04`

- [PDF page 3, Section 2.1](https://aclanthology.org/2024.tacl-1.9.pdf#page=3): NaturalQuestions-Open
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Section 2.1 checked for NaturalQuestions-Open and paragraph-long-answer subset.

## lim_07: dataset_size

Question: How many queries are selected for the controlled multi-document QA experiments?
Reference: 2,655 queries whose annotated long answer is a paragraph.
Case hash: `709cd996013e0fa92f36fde8c301ce860df063e8baa8b1601994893577f27410`

- [PDF page 3, Section 2.1](https://aclanthology.org/2024.tacl-1.9.pdf#page=3): 2655 queries
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Section 2.1 explicitly selects 2655 queries; reference uses the same count.

## lim_08: retrieval

Question: How are distractor documents retrieved in the controlled QA experiments?
Reference: Contriever fine-tuned on MS-MARCO retrieves relevant Wikipedia chunks that exclude annotated answers.
Case hash: `b9eafd8a1cad6c299b8777844457be7685278693a5f3a5fba6a4fa3f2d4fc7e6`

- [PDF page 3, Section 2.1](https://aclanthology.org/2024.tacl-1.9.pdf#page=3): Contriever, fine-tuned on MS-MARCO
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Contriever/MS-MARCO and exclusion of annotated answers checked in Section 2.1; plausible-answer ambiguity remains a paper caveat.

## lim_09: methodology

Question: How do the QA experiments vary relevant-information position and input context length?
Reference: They reorder documents to move the answer-bearing document and change the number of distractor documents.
Case hash: `4bd65f6426e4739c698b2f32ef15364e6d723b6e249f84aef42a106f04b99ee3`

- [PDF page 4, Section 2.1](https://aclanthology.org/2024.tacl-1.9.pdf#page=4): change the position
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Figures 3 and 4 plus Section 2.1 checked: reorder answer document and vary distractor count.

## lim_10: evaluation

Question: How is QA accuracy judged?
Reference: A prediction is counted as correct when it contains any annotated correct answer.
Case hash: `cb9582034bba85d06ebac3e93f4fa8cdeb57f5b8f74708fb3a6e6c682ab45fe3`

- [PDF page 4, Section 2.1](https://aclanthology.org/2024.tacl-1.9.pdf#page=4): appear in the predicted output
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Accuracy criterion checked as containment of any annotated correct answer, not full-string exact match.

## lim_11: experiments

Question: How many documents are used in the controlled multi-document QA settings?
Reference: 10, 20, and 30 total documents.
Case hash: `23e48ee02fd0bd2add031842c066e6df7b72f1948bbbfb442f1eddce1296ed70`

- [PDF page 5, Section 2.3](https://aclanthology.org/2024.tacl-1.9.pdf#page=5): 20, and 30 total documents
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Section 2.3 checked for 10, 20, and 30 total documents.

## lim_12: numeric_results

Question: What are the closed-book and oracle accuracies for GPT-3.5-Turbo in Table 1?
Reference: 56.1% closed-book accuracy and 88.3% oracle accuracy.
Case hash: `b43984c147ba9c0b198971276110b22afb9aead0754a147a8678401c9532c4d1`

- [PDF page 5, Table 1](https://aclanthology.org/2024.tacl-1.9.pdf#page=5): GPT-3.5-Turbo
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Table 1 visually inspected: GPT-3.5-Turbo row is 56.1% closed-book / 88.3% oracle; distinct from 16K row.

## lim_13: synthetic_task

Question: What do the keys and values represent in the synthetic retrieval task?
Reference: Unique randomly generated 128-bit UUIDs; the model returns the value for a specified key.
Case hash: `50be84b72937847f3fbc511505ca1615334b0ede147c9d441206d68b554e6de5`

- [PDF page 6, Figure 6 and Section 3.1](https://aclanthology.org/2024.tacl-1.9.pdf#page=6): 128-bit UUIDs
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Figure 6 and Section 3.1 checked for 128-bit unique random UUIDs and key-to-value retrieval.

## lim_14: experiments

Question: What key-value pair counts and sample sizes are used in Section 3.2?
Reference: 75, 140, and 300 pairs, with 500 examples for each setting.
Case hash: `fc414f55684532696014eaddc75c45aa002b2ba539a9f8bc3b435b943c60532d`

- [PDF page 7, Section 3.2](https://aclanthology.org/2024.tacl-1.9.pdf#page=7): 500 examples
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Section 3.2 checked for 75/140/300 pairs and 500 examples each.

## lim_15: methodology

Question: How does query-aware contextualization affect key-value retrieval versus multi-document QA?
Reference: It enables near-perfect key-value retrieval but minimally changes QA performance trends.
Case hash: `9407924c0317e298040c4ccf83b9246ebf7bbce92f6f28cf6a8b0a400f33e41c`

- [PDF page 8, Section 4.2](https://aclanthology.org/2024.tacl-1.9.pdf#page=8): near-perfect performance
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Section 4.2 checked: near-perfect key-value results and minimal changes in QA trends; does not imply QA robustness solved.

## lim_16: conclusion

Question: What does the conclusion say about reader performance compared with retriever recall?
Reference: Reader performance saturates substantially before retriever recall.
Case hash: `e4aec5b042faa7a802bfb65ae67a5e88b06a359d1735887e5236784b4d3a13ac`

- [PDF page 11, Section 7](https://aclanthology.org/2024.tacl-1.9.pdf#page=11): saturates far before retriever recall
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Section 7 conclusion checked: reader saturation precedes retriever recall saturation.

## lim_17: limitations

Question: Which decoding strategy is used, and what decoding work is left for the future?
Reference: Greedy decoding is used; other decoding methods are left for future work.
Case hash: `0233d3f5eb40e0404ebc9610e951b46489cfc95200bd01a301598a5d92c3557d`

- [PDF page 4, Section 2.2](https://aclanthology.org/2024.tacl-1.9.pdf#page=4): greedy decoding
- [PDF page 5, Section 2.2 continuation](https://aclanthology.org/2024.tacl-1.9.pdf#page=5): other decoding methods to future work
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Page reference corrected during review: greedy decoding is on PDF page 4 and future-work continuation is on page 5.

## lim_18: architecture

Question: When are encoder-decoder models relatively robust to relevant-information position?
Reference: Within their training-time context length; longer evaluation sequences exhibit positional degradation.
Case hash: `553b2ff984b5e8a345647e38a7f957e39a6fe141e2874c738c364a7c57945d52`

- [PDF page 8, Figure 8 and Section 4.1](https://aclanthology.org/2024.tacl-1.9.pdf#page=8): training-time maximum sequence length
Reviewer note: Check the complete referenced passage, including qualifiers; short anchors locate evidence and are not a full support proof.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Figure 8 and Section 4.1 checked; robustness is qualified by training-time context length.

## lim_19: unanswerable

Question: What vision-backbone training schedule does this paper prescribe?
Reference: Expected behavior: abstain; the paper does not establish this answer.
Case hash: `ab1371b71d8840fe0fa0c06b48600acb3d2cc6c3db86232e806df9c74314074c`

Reviewer note: Check the full paper scope; no such experimental specification or measurement is established.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Full-paper topic/scope checked: no vision-backbone training schedule is prescribed; expected behavior is abstention.

## lim_20: unanswerable

Question: What GPU operating temperature was measured during the experiments?
Reference: Expected behavior: abstain; the paper does not establish this answer.
Case hash: `db290cef4319af950fecbacf6f927817f2378755f2a363de0d39c64231c99620`

Reviewer note: Check the full paper scope; no such experimental specification or measurement is established.

- [x] Answer/reference checked against source.
- [x] Source pages and supporting passages checked.
- [x] Expected answerability checked.
- Reviewer / provenance / decision: Codex / assistant / approved
- Review comments: Full-paper topic/scope checked: no measured GPU operating temperature is supplied; expected behavior is abstention.
