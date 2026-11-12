# ResearchAI offline RAG evaluation

Evaluation: `b0df21fb688044af9bd2fa6b35aadbd9`
Date: 2026-11-12T07:37:02.253736+00:00
Execution status: **partial**
Dataset: lost-in-middle-20 / 1.0.0
Selected cases: 20 of 20; strategy records: 40.
Evaluated Git commit: `142f592ab40598dc170c4ec58c34832c8b517630`
Reference review provenance: assistant.
Evaluator configuration: `{"completion_gateway": "OpenRouter", "judge_model": "meta-llama/llama-3.3-70b-instruct", "manual_review_of": "9168d51ab6a54a55ad9390c2f1af3e6e", "max_embedding_inputs": 200, "max_llm_requests": 1000, "max_output_tokens": 2048, "max_samples": 20, "max_workers": 2, "metric_timeout_seconds": 180, "ragas_version": "0.2.15", "relevancy_embeddings": "Voyage query embeddings", "relevancy_questions": 3, "temperature": 0.1, "temperature_effective": 0.1, "timeout_seconds": 60}`
Request usage: `{"embedding_inputs": 100, "llm_requests": 414}`

Scores are computed metric outputs, not an overall accuracy percentage. Missing/failed values are never replaced with zero.
Unanswerable questions use abstention and manual checks rather than inappropriate reference-based metrics.
Retrieval time is shared between paired rankings; answer-chain latency excludes that shared retrieval time.

## Metric means and coverage

| Strategy | Metric | Mean | Scored | Skipped | Errors |
|---|---|---:|---:|---:|---:|
| hybrid | faithfulness | 0.9722 | 12 | 3 | 5 |
| hybrid | answer_relevancy | 0.7443 | 12 | 3 | 5 |
| hybrid | context_precision | 0.5572 | 13 | 2 | 5 |
| hybrid | context_recall | 0.9231 | 13 | 2 | 5 |
| hybrid | factual_correctness | 0.6600 | 12 | 3 | 5 |
| semantic | faithfulness | 1.0000 | 13 | 3 | 4 |
| semantic | answer_relevancy | 0.8250 | 13 | 3 | 4 |
| semantic | context_precision | 0.6208 | 14 | 2 | 4 |
| semantic | context_recall | 0.7857 | 14 | 2 | 4 |
| semantic | factual_correctness | 0.4977 | 13 | 3 | 4 |

## Paired comparison

Positive deltas favor hybrid for these measured pairs only. No general superiority claim follows from a small or incomplete benchmark.

| Metric | Paired cases | Mean hybrid − semantic |
|---|---:|---:|
| faithfulness | 10 | -0.0333 |
| answer_relevancy | 10 | -0.0384 |
| context_precision | 12 | 0.0251 |
| context_recall | 12 | 0.1667 |
| factual_correctness | 10 | -0.0150 |

## Individual results and review

### lim_01 / hybrid

Question: What is the title of the paper?
Reference: Lost in the Middle: How Language Models Use Long Contexts.
Answer: The title of the paper is “Lost in the Middle: How Language Models Use Long Contexts.” \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 3728.9730410047923, "temperature": null}`
Answer-chain latency: 2579.7 ms; shared retrieval: 3729.0 ms.
Retrieved chunk IDs: 6bad31c61787f836bee210763783ea0aa85f8d2d5b7337cd5f05c5bae5487745, 73de21b622f19de0aa0c35f7d03512e2f9b24820fbef65204ce11ddbe5a404ac, 1469219a95ce041a72602590f4ded7b0a7be00d99375ce4cf593d43b3672f04b, a9facdddbad626afbebd6b54f4b0f2878a97969d64f52ec54acf306364b66f14, b28f5492d56c4103e45c7048b03c9eb264914a6dc5ab054da6e86ab0dcbe0b8d, c66d5d5f87f2a17e79fdb6ed8433625ca59bfecb3c8f9257d1df62c84831d13c; source pages: \[\[6\], \[4\], \[10\], \[15\], \[15\], \[1\]\].
- faithfulness: 1.0
- answer_relevancy: 0.9999664504467217
- context_precision: 0.16666666665
- context_recall: 1.0
- factual_correctness: 1.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Title and page-1 heading match the PDF.

### lim_01 / semantic

Question: What is the title of the paper?
Reference: Lost in the Middle: How Language Models Use Long Contexts.
Answer: The title of the paper is “Lost in the Middle: How Language Models Use Long Contexts.” \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 3728.9730410047923, "temperature": null}`
Answer-chain latency: 2717.6 ms; shared retrieval: 3729.0 ms.
Retrieved chunk IDs: 1469219a95ce041a72602590f4ded7b0a7be00d99375ce4cf593d43b3672f04b, a9facdddbad626afbebd6b54f4b0f2878a97969d64f52ec54acf306364b66f14, c66d5d5f87f2a17e79fdb6ed8433625ca59bfecb3c8f9257d1df62c84831d13c, 73de21b622f19de0aa0c35f7d03512e2f9b24820fbef65204ce11ddbe5a404ac, 52dbbb853e914bb2491e07cc764dc7f68d563986ece84155e8991c017d99b66c, 1f060ac830fabb9d0d9f1ec4b45e6f59121399a035670a8a52088fb904fae88a; source pages: \[\[10\], \[15\], \[1\], \[4\], \[4\], \[14\]\].
- faithfulness: 1.0
- answer_relevancy: 0.9999664504467217
- context_precision: 0.3333333333
- context_recall: 1.0
- factual_correctness: 1.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Title and page-1 heading match the PDF.

### lim_02 / hybrid

Question: Who are the authors of the paper?
Reference: Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang.
Answer: The authors are Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang. \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 4432.174165995093, "temperature": null}`
Answer-chain latency: 3312.3 ms; shared retrieval: 4432.2 ms.
Retrieved chunk IDs: 92f7779125c6996575372bb48a6908f17d6f11435419bd60aeddc547e87a764a, a2b9c37507d40817c1cf998152226ffb6f0211e5ed98c0ea5398a220cdf5f875, 1bc39c762a31a36dc71e2a090209a688df00d95a88b13e6a648a3b429099b5e1, c66d5d5f87f2a17e79fdb6ed8433625ca59bfecb3c8f9257d1df62c84831d13c, f8df91d7bafc9c596d0d0c39a6002304b7ac1fe861f375048a222ca38fe4f563, 67fc2c78f8c84f5d813066953d4afbb723427f3df39db558fd7655435f30605b; source pages: \[\[11\], \[4\], \[4\], \[1\], \[4\], \[14\]\].
- faithfulness: 1.0
- answer_relevancy: 0.963188350174299
- context_precision: 0.249999999975
- context_recall: 1.0
- factual_correctness: 1.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — All seven author names match the page-1 author block; affiliations are correctly excluded.

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
Manual review (assistant, Codex): `{"answer_correct": "fail", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "not_applicable"}` — No answer was returned: generation_failed. This is a failed service outcome, not an abstention or an invented incorrect answer. No citations or contexts were preserved for this failed generation, so evidence/page/text checks are not applicable.

### lim_03 / hybrid

Question: What uncertainty about long-context language models does the paper investigate?
Reference: Whether language models can reliably find and use relevant information throughout a long input context.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual review (assistant, Codex): `{"answer_correct": "fail", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "not_applicable"}` — No answer was returned: generation_failed. This is a failed service outcome, not an abstention or an invented incorrect answer. No citations or contexts were preserved for this failed generation, so evidence/page/text checks are not applicable.

### lim_03 / semantic

Question: What uncertainty about long-context language models does the paper investigate?
Reference: Whether language models can reliably find and use relevant information throughout a long input context.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual review (assistant, Codex): `{"answer_correct": "fail", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "not_applicable"}` — No answer was returned: generation_failed. This is a failed service outcome, not an abstention or an invented incorrect answer. No citations or contexts were preserved for this failed generation, so evidence/page/text checks are not applicable.

### lim_04 / hybrid

Question: Which two tasks are used to study long-context information use?
Reference: Multi-document question answering and synthetic key-value retrieval.
Answer: The two tasks are multi-document question answering and key-value retrieval. \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 3899.698790999537, "temperature": null}`
Answer-chain latency: 2478.3 ms; shared retrieval: 3899.7 ms.
Retrieved chunk IDs: 72ec8c57faa2f4dcb0620290710f666da459bee24393c4a5732333bdb772512d, d4dbfbca532313e86d61b06d4957eeab82c91e2c143af72baeda6b0fd1964e46, ab4ee9517135e797fd7071b532b2144c831b35a1b55df7e2493aced4d4b127b5, 0d4ab915c29c37a64af76f0273193c9e0b804a5079bc0c30aec03bf297a07e35, f1bf95c9cf524520fef6f2b7d33690a2055ce66ff57de8c6fec81efaae06b4fe, 4ebe502883ad3518827b33564e7a8e0928e40a8fe784d86cd2c062bf24653361; source pages: \[\[1\], \[11\], \[11\], \[10\], \[3\], \[11\]\].
- faithfulness: 1.0
- answer_relevancy: 0.5969507152460828
- context_precision: 0.9999999999
- context_recall: 1.0
- factual_correctness: 0.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Both tasks match the page-1 abstract. The shorter wording key-value retrieval is sufficient for this question.

### lim_04 / semantic

Question: Which two tasks are used to study long-context information use?
Reference: Multi-document question answering and synthetic key-value retrieval.
Answer: The two tasks are multi-document question answering and key-value retrieval. \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 3899.698790999537, "temperature": null}`
Answer-chain latency: 2497.3 ms; shared retrieval: 3899.7 ms.
Retrieved chunk IDs: 72ec8c57faa2f4dcb0620290710f666da459bee24393c4a5732333bdb772512d, 4ebe502883ad3518827b33564e7a8e0928e40a8fe784d86cd2c062bf24653361, 0d4ab915c29c37a64af76f0273193c9e0b804a5079bc0c30aec03bf297a07e35, 081c07d4c71b7a7796f2e8078e09113c92cc67becf9ea318f202f29ad7c7a1fb, f1bf95c9cf524520fef6f2b7d33690a2055ce66ff57de8c6fec81efaae06b4fe, d4dbfbca532313e86d61b06d4957eeab82c91e2c143af72baeda6b0fd1964e46; source pages: \[\[1\], \[11\], \[10\], \[3\], \[3\], \[11\]\].
- faithfulness: 1.0
- answer_relevancy: 0.5969507152460828
- context_precision: 0.7499999999625
- context_recall: 0.0
- factual_correctness: 0.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Both tasks match the page-1 abstract. The shorter wording key-value retrieval is sufficient for this question.

### lim_05 / hybrid

Question: Where in a long context is relevant information generally used best and worst?
Reference: Performance is generally best near the beginning or end and worse in the middle.
Answer: Relevant information in a long context is generally used best when it appears at the beginning or end, and worst when it appears in the middle. \[1\] \[2\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 3128.771332994802, "temperature": null}`
Answer-chain latency: 4177.0 ms; shared retrieval: 3128.8 ms.
Retrieved chunk IDs: f1bf95c9cf524520fef6f2b7d33690a2055ce66ff57de8c6fec81efaae06b4fe, 72ec8c57faa2f4dcb0620290710f666da459bee24393c4a5732333bdb772512d, f830aae028e07465ee010c0e6c02e30b6c354b31ae757e64d6dd5c946f48aecc, d4dbfbca532313e86d61b06d4957eeab82c91e2c143af72baeda6b0fd1964e46, 3d226376378c7ff78047e1fb53a6d3aa0f9e5feda44e98390359a00e111eab51, c87aada4bbd90bfe5de4ae5194df3b0364dd2813133a1d55359de87768906c50; source pages: \[\[3\], \[1\], \[2\], \[11\], \[9\], \[8\]\].
- faithfulness: 1.0
- answer_relevancy: 0.9254196366246704
- context_precision: 0.9999999999833333
- context_recall: 1.0
- factual_correctness: 1.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Beginning/end versus middle trend agrees with the abstract and introduction on PDF pages 1–2.

### lim_05 / semantic

Question: Where in a long context is relevant information generally used best and worst?
Reference: Performance is generally best near the beginning or end and worse in the middle.
Answer: Relevant information in a long context is generally used best when it appears at the very beginning or the very end, and worst when it appears in the middle. \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 3128.771332994802, "temperature": null}`
Answer-chain latency: 3032.0 ms; shared retrieval: 3128.8 ms.
Retrieved chunk IDs: 72ec8c57faa2f4dcb0620290710f666da459bee24393c4a5732333bdb772512d, f1bf95c9cf524520fef6f2b7d33690a2055ce66ff57de8c6fec81efaae06b4fe, f830aae028e07465ee010c0e6c02e30b6c354b31ae757e64d6dd5c946f48aecc, 4ebe502883ad3518827b33564e7a8e0928e40a8fe784d86cd2c062bf24653361, d4dbfbca532313e86d61b06d4957eeab82c91e2c143af72baeda6b0fd1964e46, 66940e5044b883564f960e5645f6d4fa9ca0f4155dfad86f90edd9644fcddf30; source pages: \[\[1\], \[3\], \[2\], \[11\], \[11\], \[1, 2\]\].
- faithfulness: 1.0
- answer_relevancy: 0.924297104809384
- context_precision: 0.9999999999833333
- context_recall: 1.0
- factual_correctness: 1.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Beginning/end versus middle trend agrees with the abstract and introduction on PDF pages 1–2.

### lim_06 / hybrid

Question: Which question-answering dataset is used for the controlled multi-document QA task?
Reference: NaturalQuestions-Open, using questions with paragraph long answers.
Answer: I couldn’t find enough evidence in this document to answer that question.
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 4004.6195840041037, "temperature": null}`
Answer-chain latency: 2343.1 ms; shared retrieval: 4004.6 ms.
Retrieved chunk IDs: 081c07d4c71b7a7796f2e8078e09113c92cc67becf9ea318f202f29ad7c7a1fb, fb0421f20e7333b9f9d470d7aa85c5e88f3d70e704cd3d2caad8ed00c6f8a898, 2e68bcf4d552ef79f9110bab7342e6e78c17e80ce49ba5f019534f5e524dfdaa, 426659be570c68c825e1b5e35fabf27c58151133a7f9a29244e4d6d5533e134c, 8db234810fe5cc92665f500c3b4245d828f87073d5cbc319649791fd25c40cff, c96ab297a61979ba63155abef5dafb9ec9e162c7daf7e4c923f932d21dc81a7e; source pages: \[\[3\], \[15\], \[3\], \[9\], \[2\], \[2\]\].
- faithfulness: skipped (abstention_has_no_factual_answer)
- answer_relevancy: skipped (abstention_has_no_factual_answer)
- factual_correctness: skipped (abstention_has_no_factual_answer)
- context_precision: 0.0
- context_recall: 0.0
Deterministic checks: `{"answerability_correct": false, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual review (assistant, Codex): `{"answer_correct": "fail", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "fail"}` — False abstention: the reference is supported by Section 2.1, PDF page 3 (NaturalQuestions-Open). No factual answer/citation was returned.

### lim_06 / semantic

Question: Which question-answering dataset is used for the controlled multi-document QA task?
Reference: NaturalQuestions-Open, using questions with paragraph long answers.
Answer: The controlled multi-document question-answering task uses the NaturalQuestions-Open dataset. \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 4004.6195840041037, "temperature": null}`
Answer-chain latency: 2849.0 ms; shared retrieval: 4004.6 ms.
Retrieved chunk IDs: 2e68bcf4d552ef79f9110bab7342e6e78c17e80ce49ba5f019534f5e524dfdaa, fb0421f20e7333b9f9d470d7aa85c5e88f3d70e704cd3d2caad8ed00c6f8a898, 213729e5fafea43d4daea9e7a2781ffbcaf808d8178ac1a5a32f2ecfac5ed4db, b28f5492d56c4103e45c7048b03c9eb264914a6dc5ab054da6e86ab0dcbe0b8d, 8db234810fe5cc92665f500c3b4245d828f87073d5cbc319649791fd25c40cff, 081c07d4c71b7a7796f2e8078e09113c92cc67becf9ea318f202f29ad7c7a1fb; source pages: \[\[3\], \[15\], \[3\], \[15\], \[2\], \[3\]\].
- faithfulness: 1.0
- answer_relevancy: 0.9672149386423063
- context_precision: 0.4166666666458333
- context_recall: 1.0
- factual_correctness: 0.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — NaturalQuestions-Open agrees with Section 2.1 on PDF page 3. The answer names the correct dataset but does not mention the paragraph-long-answer subset in the reference.

### lim_07 / hybrid

Question: How many queries are selected for the controlled multi-document QA experiments?
Reference: 2,655 queries whose annotated long answer is a paragraph.
Answer: The controlled multi-document QA experiments select 2,655 queries. \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 4275.361375002831, "temperature": null}`
Answer-chain latency: 3011.8 ms; shared retrieval: 4275.4 ms.
Retrieved chunk IDs: fb0421f20e7333b9f9d470d7aa85c5e88f3d70e704cd3d2caad8ed00c6f8a898, 081c07d4c71b7a7796f2e8078e09113c92cc67becf9ea318f202f29ad7c7a1fb, 8db234810fe5cc92665f500c3b4245d828f87073d5cbc319649791fd25c40cff, f4e08b09d9cc9f629151698957a2d41a70da7173f9bc9b5df7655eba3d973893, 889eba258939dd66e46aa8a63a238ce3c39d7a7e220b72038227983a1c3c5cdd, 213729e5fafea43d4daea9e7a2781ffbcaf808d8178ac1a5a32f2ecfac5ed4db; source pages: \[\[15\], \[3\], \[2\], \[16\], \[15, 16\], \[3\]\].
- faithfulness: 1.0
- answer_relevancy: 0.9883254829467485
- context_precision: 0.16666666665
- context_recall: 1.0
- factual_correctness: 0.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — The count 2,655 agrees with Section 2.1 on PDF page 3. The question asks the count; the paragraph-subset qualifier is not repeated.

### lim_07 / semantic

Question: How many queries are selected for the controlled multi-document QA experiments?
Reference: 2,655 queries whose annotated long answer is a paragraph.
Answer: 500 queries are selected for the controlled multi-document QA experiments. \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 4275.361375002831, "temperature": null}`
Answer-chain latency: 3776.6 ms; shared retrieval: 4275.4 ms.
Retrieved chunk IDs: fb0421f20e7333b9f9d470d7aa85c5e88f3d70e704cd3d2caad8ed00c6f8a898, 2e68bcf4d552ef79f9110bab7342e6e78c17e80ce49ba5f019534f5e524dfdaa, 8db234810fe5cc92665f500c3b4245d828f87073d5cbc319649791fd25c40cff, f4e08b09d9cc9f629151698957a2d41a70da7173f9bc9b5df7655eba3d973893, ad54ec0c0c346911f6f442b4c9d8fb84d159e7b214a31a5b6926f67e70360355, e28061d534284a899a7d6723ba114fc17a03a9704a42ca3e2902e6bfef5822b2; source pages: \[\[15\], \[3\], \[2\], \[16\], \[15\], \[8, 9\]\].
- faithfulness: 1.0
- answer_relevancy: 0.9999576136061844
- context_precision: 0.0
- context_recall: 0.0
- factual_correctness: 0.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "fail", "citation_pages": "fail", "evidence_support": "fail", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Wrong experiment scope: 500 is the GPT-4 appendix subset/figure-15 label on PDF page 16. The main controlled QA selection is 2,655 queries on PDF page 3. The quote really exists on page 16, so text matching passes, but it does not justify the answer to this benchmark question. Page 16 was also visually checked.

### lim_08 / hybrid

Question: How are distractor documents retrieved in the controlled QA experiments?
Reference: Contriever fine-tuned on MS-MARCO retrieves relevant Wikipedia chunks that exclude annotated answers.
Answer: In the main controlled QA experiments, distractors are retrieved using Contriever, fine-tuned on MS-MARCO. It retrieves the k−1 Wikipedia chunks most relevant to the query, excluding chunks containing any NaturalQuestions-annotated answers. \[1\]<br><br>The retrieved distractors are normally presented in decreasing order of relevance. A separate experiment randomly shuffles the k−1 distractors and states that the search results are randomly ordered. \[2\] \[3\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 2931.8261250009527, "temperature": null}`
Answer-chain latency: 5145.0 ms; shared retrieval: 2931.8 ms.
Retrieved chunk IDs: fb0421f20e7333b9f9d470d7aa85c5e88f3d70e704cd3d2caad8ed00c6f8a898, 889eba258939dd66e46aa8a63a238ce3c39d7a7e220b72038227983a1c3c5cdd, c0d4ad448c75302ef25c5597093deb9a18a8d08592eba45a8e7c5b338d57194c, b28f5492d56c4103e45c7048b03c9eb264914a6dc5ab054da6e86ab0dcbe0b8d, 213729e5fafea43d4daea9e7a2781ffbcaf808d8178ac1a5a32f2ecfac5ed4db, 41f5f9c4d085f647ee3711f0ea093167e784e3ded6fe4a274b45721f7495c678; source pages: \[\[15\], \[15, 16\], \[3\], \[15\], \[3\], \[4\]\].
- faithfulness: 1.0
- answer_relevancy: 0.88645209730135
- context_precision: 0.19999999998
- context_recall: 1.0
- factual_correctness: 0.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Contriever, MS-MARCO fine-tuning and exclusion of annotated answers agree with Section 2.1 on PDF page 3. Hybrid also distinguishes normal decreasing relevance (page 4) from the shuffled appendix variant (pages 15–16).

### lim_08 / semantic

Question: How are distractor documents retrieved in the controlled QA experiments?
Reference: Contriever fine-tuned on MS-MARCO retrieves relevant Wikipedia chunks that exclude annotated answers.
Answer: In the controlled QA experiments, distractors are retrieved using Contriever, fine-tuned on MS-MARCO. For each query, it selects the k−1 Wikipedia chunks most relevant to the query, excluding any chunks containing NaturalQuestions-annotated answers. \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 2931.8261250009527, "temperature": null}`
Answer-chain latency: 3592.1 ms; shared retrieval: 2931.8 ms.
Retrieved chunk IDs: fb0421f20e7333b9f9d470d7aa85c5e88f3d70e704cd3d2caad8ed00c6f8a898, 213729e5fafea43d4daea9e7a2781ffbcaf808d8178ac1a5a32f2ecfac5ed4db, c0d4ad448c75302ef25c5597093deb9a18a8d08592eba45a8e7c5b338d57194c, 889eba258939dd66e46aa8a63a238ce3c39d7a7e220b72038227983a1c3c5cdd, ad54ec0c0c346911f6f442b4c9d8fb84d159e7b214a31a5b6926f67e70360355, 2e68bcf4d552ef79f9110bab7342e6e78c17e80ce49ba5f019534f5e524dfdaa; source pages: \[\[15\], \[3\], \[3\], \[15, 16\], \[15\], \[3\]\].
- faithfulness: 1.0
- answer_relevancy: 0.9089930347169549
- context_precision: 0.49999999995
- context_recall: 1.0
- factual_correctness: 0.4
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Contriever, MS-MARCO fine-tuning and exclusion of annotated answers agree with Section 2.1 on PDF page 3. Hybrid also distinguishes normal decreasing relevance (page 4) from the shuffled appendix variant (pages 15–16).

### lim_09 / hybrid

Question: How do the QA experiments vary relevant-information position and input context length?
Reference: They reorder documents to move the answer-bearing document and change the number of distractor documents.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual review (assistant, Codex): `{"answer_correct": "fail", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "not_applicable"}` — No answer was returned: generation_failed. This is a failed service outcome, not an abstention or an invented incorrect answer. No citations or contexts were preserved for this failed generation, so evidence/page/text checks are not applicable.

### lim_09 / semantic

Question: How do the QA experiments vary relevant-information position and input context length?
Reference: They reorder documents to move the answer-bearing document and change the number of distractor documents.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual review (assistant, Codex): `{"answer_correct": "fail", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "not_applicable"}` — No answer was returned: generation_failed. This is a failed service outcome, not an abstention or an invented incorrect answer. No citations or contexts were preserved for this failed generation, so evidence/page/text checks are not applicable.

### lim_10 / hybrid

Question: How is QA accuracy judged?
Reference: A prediction is counted as correct when it contains any annotated correct answer.
Answer: QA reader accuracy is judged by checking whether any of the annotated answers appear in the model’s predicted output. \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 3499.3119169957936, "temperature": null}`
Answer-chain latency: 4298.7 ms; shared retrieval: 3499.3 ms.
Retrieved chunk IDs: ad54ec0c0c346911f6f442b4c9d8fb84d159e7b214a31a5b6926f67e70360355, facb3e16b41d0f95a99afcfee553b6b692ea2a3071aa17c47d100f835d695a1f, d6cab39bb0e5ae7b1b20d6df57f16f35b12c61a5fea858f35c8474a1ccf947a3, 0d4ab915c29c37a64af76f0273193c9e0b804a5079bc0c30aec03bf297a07e35, 3e3e69ed08ff72971a0289823f35c39ac16f19811f171a843de0d64951e0267c, d61089753d3ad52c003942b253af50b8fc3f4063a948518966b6c75cc204ce5a; source pages: \[\[15\], \[5\], \[10\], \[10\], \[5\], \[9\]\].
- faithfulness: 1.0
- answer_relevancy: 0.8861709546213404
- context_precision: 0.3333333333
- context_recall: 1.0
- factual_correctness: 1.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 0.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Answer-containment criterion agrees with the full sentence spanning PDF page 4 and the reader-accuracy definition on page 10. The cited page-10 wording supports the answer.

### lim_10 / semantic

Question: How is QA accuracy judged?
Reference: A prediction is counted as correct when it contains any annotated correct answer.
Answer: QA accuracy is judged by whether any of the annotated answers appear in the model’s predicted output. \[1\]<br><br>The paper uses accuracy as its primary evaluation metric. \[2\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 3499.3119169957936, "temperature": null}`
Answer-chain latency: 3368.0 ms; shared retrieval: 3499.3 ms.
Retrieved chunk IDs: facb3e16b41d0f95a99afcfee553b6b692ea2a3071aa17c47d100f835d695a1f, 3e3e69ed08ff72971a0289823f35c39ac16f19811f171a843de0d64951e0267c, 41f5f9c4d085f647ee3711f0ea093167e784e3ded6fe4a274b45721f7495c678, 906463fa71c3effa61b6cc45e9147986750210f80a05fd0c989227c61ae6f0bc, ad54ec0c0c346911f6f442b4c9d8fb84d159e7b214a31a5b6926f67e70360355, d6cab39bb0e5ae7b1b20d6df57f16f35b12c61a5fea858f35c8474a1ccf947a3; source pages: \[\[5\], \[5\], \[4\], \[15\], \[15\], \[10\]\].
- faithfulness: 1.0
- answer_relevancy: 0.9999606603180612
- context_precision: 0.33333333331666665
- context_recall: 1.0
- factual_correctness: 0.67
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Answer-containment criterion agrees with the full sentence spanning PDF page 4 and the reader-accuracy definition on page 10. The cited page-10 wording supports the answer.

### lim_11 / hybrid

Question: How many documents are used in the controlled multi-document QA settings?
Reference: 10, 20, and 30 total documents.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual review (assistant, Codex): `{"answer_correct": "fail", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "not_applicable"}` — No answer was returned: generation_failed. This is a failed service outcome, not an abstention or an invented incorrect answer. No citations or contexts were preserved for this failed generation, so evidence/page/text checks are not applicable.

### lim_11 / semantic

Question: How many documents are used in the controlled multi-document QA settings?
Reference: 10, 20, and 30 total documents.
Answer: The controlled multi-document QA settings use 20 documents in each input context. \[1\] \[2\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 3783.720292005455, "temperature": null}`
Answer-chain latency: 3019.2 ms; shared retrieval: 3783.7 ms.
Retrieved chunk IDs: fb0421f20e7333b9f9d470d7aa85c5e88f3d70e704cd3d2caad8ed00c6f8a898, f4e08b09d9cc9f629151698957a2d41a70da7173f9bc9b5df7655eba3d973893, 2e68bcf4d552ef79f9110bab7342e6e78c17e80ce49ba5f019534f5e524dfdaa, 735f9a7a53bc23596ec61356477a2311a34af134df6b7f7c03a30c4cbbb14c44, 7de5476c91b60e65687c2e84fff5cbb9aec33fb1046ad9c53cf52638ae6f5c11, 8db234810fe5cc92665f500c3b4245d828f87073d5cbc319649791fd25c40cff; source pages: \[\[15\], \[16\], \[3\], \[10\], \[15, 16\], \[2\]\].
- faithfulness: 1.0
- answer_relevancy: 0.8924988464105081
- context_precision: 0.9999999999
- context_recall: 1.0
- factual_correctness: 0.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 0.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "fail", "citation_pages": "fail", "evidence_support": "fail", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Incomplete and overgeneralized: the answer gives only the 20-document appendix setting on PDF page 16. Section 2.3 on PDF page 5 specifies 10, 20 and 30 total documents. Both quoted page-16 passages exist, but they do not establish the full controlled experiment settings. Page 16 was also visually checked.

### lim_12 / hybrid

Question: What are the closed-book and oracle accuracies for GPT-3.5-Turbo in Table 1?
Reference: 56.1% closed-book accuracy and 88.3% oracle accuracy.
Answer: GPT-3.5-Turbo has a closed-book accuracy of 56.1% and an oracle accuracy of 88.3% in Table 1. \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 2575.9733750019222, "temperature": null}`
Answer-chain latency: 2653.6 ms; shared retrieval: 2576.0 ms.
Retrieved chunk IDs: 3e3e69ed08ff72971a0289823f35c39ac16f19811f171a843de0d64951e0267c, 3f2e10089a814861cfd854f5c8a66e3fdeb2455ac422e96ed9f8ae1afc61d7d7, facb3e16b41d0f95a99afcfee553b6b692ea2a3071aa17c47d100f835d695a1f, 5f385c66d12dd12a550e7502a9fb94f1464ffe0dafe10f9c1929d39f6be991a6, 3a139c0dd6698f14580f596952007b891a89b297f13bf02399ab91770fb9de72, 7c8409cea6217df0bd169b7ed262f61da58a3f9db6b9d87e9ec496e09249cb1a; source pages: \[\[5\], \[2\], \[5\], \[5\], \[16\], \[15\]\].
- faithfulness: 1.0
- answer_relevancy: 0.9938738465375772
- context_precision: 0.9999999999
- context_recall: 1.0
- factual_correctness: 1.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Both numbers and their column labels match Table 1 on PDF page 5; these percentages describe the source experiment, not this RAG benchmark.

### lim_12 / semantic

Question: What are the closed-book and oracle accuracies for GPT-3.5-Turbo in Table 1?
Reference: 56.1% closed-book accuracy and 88.3% oracle accuracy.
Answer: GPT-3.5-Turbo has a closed-book accuracy of 56.1% and an oracle accuracy of 88.3% in Table 1. \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 2575.9733750019222, "temperature": null}`
Answer-chain latency: 2552.1 ms; shared retrieval: 2576.0 ms.
Retrieved chunk IDs: 3e3e69ed08ff72971a0289823f35c39ac16f19811f171a843de0d64951e0267c, 3f2e10089a814861cfd854f5c8a66e3fdeb2455ac422e96ed9f8ae1afc61d7d7, facb3e16b41d0f95a99afcfee553b6b692ea2a3071aa17c47d100f835d695a1f, 906463fa71c3effa61b6cc45e9147986750210f80a05fd0c989227c61ae6f0bc, 7c8409cea6217df0bd169b7ed262f61da58a3f9db6b9d87e9ec496e09249cb1a, 6024bcc7f4764e1b9598d2b34c4dbf9871d9db03fc9f48ce37f3184d5cc35360; source pages: \[\[5\], \[2\], \[5\], \[15\], \[15\], \[8, 9\]\].
- faithfulness: 1.0
- answer_relevancy: 0.9938738465375772
- context_precision: 0.9999999999
- context_recall: 1.0
- factual_correctness: 1.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Both numbers and their column labels match Table 1 on PDF page 5; these percentages describe the source experiment, not this RAG benchmark.

### lim_13 / hybrid

Question: What do the keys and values represent in the synthetic retrieval task?
Reference: Unique randomly generated 128-bit UUIDs; the model returns the value for a specified key.
Answer: The keys and values are unique, randomly generated 128-bit UUIDs. The input consists of a JSON object containing k key-value pairs and a specified key from that object. \[1\] \[2\]<br><br>The task is to return the value associated with the specified key; one pair is relevant, while the remaining k−1 pairs are irrelevant distractors. \[3\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 4948.508624998794, "temperature": null}`
Answer-chain latency: 4627.9 ms; shared retrieval: 4948.5 ms.
Retrieved chunk IDs: bfe5c7e91e9fcfe2110342eec74630e8f32dc41316702f1e9a47b04b2a704ba6, c96ab297a61979ba63155abef5dafb9ec9e162c7daf7e4c923f932d21dc81a7e, 1cd1a8d5a4bca4ad1b700c073497aa0fa386ec57704281cf1cf5410b60d177bb, 6bad31c61787f836bee210763783ea0aa85f8d2d5b7337cd5f05c5bae5487745, f0e9e5d64721664116ad4488a74177addbc148729a054674e7344cafd2738929, b5d45de6e9db117383ccb2fc7fa9722b47d31bf2056f6f16ef4a30044acbc08a; source pages: \[\[6\], \[2\], \[6\], \[6\], \[7\], \[6\]\].
- faithfulness: 0.6666666666666666
- answer_relevancy: 0.37384623051162813
- context_precision: 0.8766666666491334
- context_recall: 1.0
- factual_correctness: 0.25
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Unique random UUID keys/values and return-the-associated-value task agree with Section 3.1 on PDF page 6. Hybrid also cites the 128-bit figure caption; semantic omits that bit-width detail while correctly answering the task meaning.

### lim_13 / semantic

Question: What do the keys and values represent in the synthetic retrieval task?
Reference: Unique randomly generated 128-bit UUIDs; the model returns the value for a specified key.
Answer: In the synthetic retrieval task, the keys and values are unique, randomly generated UUID strings. The input consists of a JSON object containing k key-value pairs and a specified key from that object. \[1\]<br><br>The task is to return the value associated with the specified key; the other k − 1 pairs are irrelevant distractors. \[2\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 4948.508624998794, "temperature": null}`
Answer-chain latency: 4281.6 ms; shared retrieval: 4948.5 ms.
Retrieved chunk IDs: bfe5c7e91e9fcfe2110342eec74630e8f32dc41316702f1e9a47b04b2a704ba6, 1cd1a8d5a4bca4ad1b700c073497aa0fa386ec57704281cf1cf5410b60d177bb, c96ab297a61979ba63155abef5dafb9ec9e162c7daf7e4c923f932d21dc81a7e, f0e9e5d64721664116ad4488a74177addbc148729a054674e7344cafd2738929, 6bad31c61787f836bee210763783ea0aa85f8d2d5b7337cd5f05c5bae5487745, ce6a6651697f4fd7188497f59125dee7ce27e1bc3fbb7865e924e649a8dbbdea; source pages: \[\[6\], \[6\], \[2\], \[7\], \[6\], \[7\]\].
- faithfulness: 1.0
- answer_relevancy: 0.6109734410985265
- context_precision: 0.8041666666465626
- context_recall: 1.0
- factual_correctness: 0.33
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Unique random UUID keys/values and return-the-associated-value task agree with Section 3.1 on PDF page 6. Hybrid also cites the 128-bit figure caption; semantic omits that bit-width detail while correctly answering the task meaning.

### lim_14 / hybrid

Question: What key-value pair counts and sample sizes are used in Section 3.2?
Reference: 75, 140, and 300 pairs, with 500 examples for each setting.
Answer: Section 3.2 uses input contexts containing 75, 140, and 300 key-value pairs, with 500 examples for each setting. \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 4121.628541994141, "temperature": null}`
Answer-chain latency: 3187.5 ms; shared retrieval: 4121.6 ms.
Retrieved chunk IDs: bfe5c7e91e9fcfe2110342eec74630e8f32dc41316702f1e9a47b04b2a704ba6, ce6a6651697f4fd7188497f59125dee7ce27e1bc3fbb7865e924e649a8dbbdea, 9a8a70194feeded359ebfa55d30b1f561f2c05fa66702f67e6280414460517ac, 4b586a1a72cda92e3a357c9fed7b17f9ab4dfe560ee224ebbc0968ee996f6951, fb8d1648a7a01eec047af7c0ca1ef4b36256a94657296a9cb8d9a6f99e3c8587, f4e08b09d9cc9f629151698957a2d41a70da7173f9bc9b5df7655eba3d973893; source pages: \[\[6\], \[7\], \[7\], \[7\], \[7\], \[16\]\].
- faithfulness: 1.0
- answer_relevancy: 0.44863319400673324
- context_precision: 0.249999999975
- context_recall: 1.0
- factual_correctness: 1.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — 75, 140, 300 pairs and 500 examples per setting agree with Section 3.2 on PDF page 7.

### lim_14 / semantic

Question: What key-value pair counts and sample sizes are used in Section 3.2?
Reference: 75, 140, and 300 pairs, with 500 examples for each setting.
Answer: I couldn’t find enough evidence in this document to answer that question.
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 4121.628541994141, "temperature": null}`
Answer-chain latency: 4104.5 ms; shared retrieval: 4121.6 ms.
Retrieved chunk IDs: ce6a6651697f4fd7188497f59125dee7ce27e1bc3fbb7865e924e649a8dbbdea, 9a8a70194feeded359ebfa55d30b1f561f2c05fa66702f67e6280414460517ac, dc9a307c4195bde2e1be3d3815ea36839caa039d3112e28c7a1f98ca314c8a40, fb8d1648a7a01eec047af7c0ca1ef4b36256a94657296a9cb8d9a6f99e3c8587, 91ead4a79e08e8aa5ae66ae2bf9c32cecf2de6c653c02ec54a11d189e0730e96, 01898750abc58013db5cedbaac74d4d7a1925ce7aafc592342138a64979b1939; source pages: \[\[7\], \[7\], \[8\], \[7\], \[5\], \[5\]\].
- faithfulness: skipped (abstention_has_no_factual_answer)
- answer_relevancy: skipped (abstention_has_no_factual_answer)
- factual_correctness: skipped (abstention_has_no_factual_answer)
- context_precision: 0.0
- context_recall: 0.0
Deterministic checks: `{"answerability_correct": false, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual review (assistant, Codex): `{"answer_correct": "fail", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "fail"}` — False abstention: the reference is supported by Section 3.2, PDF page 7 (75, 140 and 300 pairs; 500 examples each). No factual answer/citation was returned.

### lim_15 / hybrid

Question: How does query-aware contextualization affect key-value retrieval versus multi-document QA?
Reference: It enables near-perfect key-value retrieval but minimally changes QA performance trends.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual review (assistant, Codex): `{"answer_correct": "fail", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "not_applicable"}` — No answer was returned: generation_failed. This is a failed service outcome, not an abstention or an invented incorrect answer. No citations or contexts were preserved for this failed generation, so evidence/page/text checks are not applicable.

### lim_15 / semantic

Question: How does query-aware contextualization affect key-value retrieval versus multi-document QA?
Reference: It enables near-perfect key-value retrieval but minimally changes QA performance trends.
Answer: Query-aware contextualization dramatically improves key-value retrieval, producing near-perfect results across 75, 140, and 300 key-value pairs; GPT-3.5-Turbo achieves perfect performance with 300 pairs. \[1\]<br><br>For multi-document QA, query-aware contextualization has little effect on overall performance trends: it slightly helps when the relevant information is at the beginning of the context, but slightly hurts in other positions. \[2\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 3767.5618330031284, "temperature": null}`
Answer-chain latency: 4135.3 ms; shared retrieval: 3767.6 ms.
Retrieved chunk IDs: 5cba8423397451ad35023f8930f18ce0c1bd13b0f936fb9cc8e62c1706750826, aa07a5bb6bcf30ef0516bbacfca4a8d3f6357f0bd25053db441897dcf529b3e7, c96ab297a61979ba63155abef5dafb9ec9e162c7daf7e4c923f932d21dc81a7e, b5d45de6e9db117383ccb2fc7fa9722b47d31bf2056f6f16ef4a30044acbc08a, 6bad31c61787f836bee210763783ea0aa85f8d2d5b7337cd5f05c5bae5487745, df510f0401ffdec6e078029ac49ff2a010ddc0ada3a449b912836e76c55853fd; source pages: \[\[8\], \[8\], \[2\], \[6\], \[6\], \[2, 3\]\].
- faithfulness: 1.0
- answer_relevancy: 0.9613140860014119
- context_precision: 0.9999999999833333
- context_recall: 1.0
- factual_correctness: 0.4
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — The key-value versus QA contrast agrees with Section 4.2 on PDF page 8. The perfect-300-pair example is specifically GPT-3.5-Turbo (16K), as the quote states; the answer abbreviates the model name. This qualifier should be retained in a stronger answer.

### lim_16 / hybrid

Question: What does the conclusion say about reader performance compared with retriever recall?
Reference: Reader performance saturates substantially before retriever recall.
Answer: The conclusion says that language-model reader performance saturates far before retriever recall, meaning readers do not effectively benefit from much of the additional retrieved context. \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 3408.1088329985505, "temperature": null}`
Answer-chain latency: 2789.2 ms; shared retrieval: 3408.1 ms.
Retrieved chunk IDs: d6cab39bb0e5ae7b1b20d6df57f16f35b12c61a5fea858f35c8474a1ccf947a3, f8b9448e01f346b54655d12f36eff318a36018ba6ad6cd06b54ee444ebb14367, efc6ebed2a7f37a0df45aeaed1f1303ec202a1ce7a7f7b6f8fcde5e7058db5bd, d4dbfbca532313e86d61b06d4957eeab82c91e2c143af72baeda6b0fd1964e46, c96ab297a61979ba63155abef5dafb9ec9e162c7daf7e4c923f932d21dc81a7e, d61089753d3ad52c003942b253af50b8fc3f4063a948518966b6c75cc204ce5a; source pages: \[\[10\], \[10\], \[3\], \[11\], \[2\], \[9\]\].
- faithfulness: 1.0
- answer_relevancy: 0.8685928042907106
- context_precision: 0.999999999975
- context_recall: 1.0
- factual_correctness: 0.67
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Reader saturation before retriever recall matches the PDF page-11 conclusion; the extra-context interpretation also agrees with the practical case-study description on page 3.

### lim_16 / semantic

Question: What does the conclusion say about reader performance compared with retriever recall?
Reference: Reader performance saturates substantially before retriever recall.
Answer: The conclusion says that language-model reader performance saturates far before retriever recall, meaning readers do not effectively use additional retrieved context. \[1\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 3408.1088329985505, "temperature": null}`
Answer-chain latency: 2802.6 ms; shared retrieval: 3408.1 ms.
Retrieved chunk IDs: d6cab39bb0e5ae7b1b20d6df57f16f35b12c61a5fea858f35c8474a1ccf947a3, f8b9448e01f346b54655d12f36eff318a36018ba6ad6cd06b54ee444ebb14367, 5cba8423397451ad35023f8930f18ce0c1bd13b0f936fb9cc8e62c1706750826, d4dbfbca532313e86d61b06d4957eeab82c91e2c143af72baeda6b0fd1964e46, efc6ebed2a7f37a0df45aeaed1f1303ec202a1ce7a7f7b6f8fcde5e7058db5bd, ad54ec0c0c346911f6f442b4c9d8fb84d159e7b214a31a5b6926f67e70360355; source pages: \[\[10\], \[10\], \[8\], \[11\], \[3\], \[15\]\].
- faithfulness: 1.0
- answer_relevancy: 0.8684963622696725
- context_precision: 0.8874999999778125
- context_recall: 1.0
- factual_correctness: 0.67
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — Reader saturation before retriever recall matches the PDF page-11 conclusion; the extra-context interpretation also agrees with the practical case-study description on page 3.

### lim_17 / hybrid

Question: Which decoding strategy is used, and what decoding work is left for the future?
Reference: Greedy decoding is used; other decoding methods are left for future work.
Answer: The study uses greedy decoding when generating outputs. \[1\]<br><br>Exploration of other decoding methods is left for future work. \[2\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 3089.7283340018475, "temperature": null}`
Answer-chain latency: 2846.1 ms; shared retrieval: 3089.7 ms.
Retrieved chunk IDs: 52dbbb853e914bb2491e07cc764dc7f68d563986ece84155e8991c017d99b66c, 61dd408f0412b2562805adab453a73b250e76e1cb0904c348f3d4cf3bec414c0, 44ce30adbb0f79c9b399d10b094449d355f65bc9a95b6f8b5eab6a13d0708b07, c87aada4bbd90bfe5de4ae5194df3b0364dd2813133a1d55359de87768906c50, f1bf95c9cf524520fef6f2b7d33690a2055ce66ff57de8c6fec81efaae06b4fe, a6d810c170ed501b259df2c1d28c5fca5bf45658e92601ba8a83682d0cba543a; source pages: \[\[4\], \[5\], \[5\], \[8\], \[3\], \[8\]\].
- faithfulness: 1.0
- answer_relevancy: 0.0
- context_precision: 0.9999999999666667
- context_recall: 1.0
- factual_correctness: 1.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — The first citation locates greedy decoding on PDF page 4; the continuation on page 5 explicitly leaves other decoding methods to future work. Both pages are needed and are cited.

### lim_17 / semantic

Question: Which decoding strategy is used, and what decoding work is left for the future?
Reference: Greedy decoding is used; other decoding methods are left for future work.
Answer: The study uses greedy decoding when generating outputs. \[1\]<br><br>Exploration of other decoding methods is left for future work. \[2\]
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 3089.7283340018475, "temperature": null}`
Answer-chain latency: 4086.8 ms; shared retrieval: 3089.7 ms.
Retrieved chunk IDs: 52dbbb853e914bb2491e07cc764dc7f68d563986ece84155e8991c017d99b66c, 77daee09225aeac1d65f5e7ca5f7943355dd2d8c5f3fb9b78cd9ec4489717bff, c87aada4bbd90bfe5de4ae5194df3b0364dd2813133a1d55359de87768906c50, a6d810c170ed501b259df2c1d28c5fca5bf45658e92601ba8a83682d0cba543a, df510f0401ffdec6e078029ac49ff2a010ddc0ada3a449b912836e76c55853fd, 44ce30adbb0f79c9b399d10b094449d355f65bc9a95b6f8b5eab6a13d0708b07; source pages: \[\[4\], \[7\], \[8\], \[8\], \[2, 3\], \[5\]\].
- faithfulness: 1.0
- answer_relevancy: 0.0
- context_precision: 0.6666666666333333
- context_recall: 1.0
- factual_correctness: 1.0
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": 1.0, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "pass", "evidence_support": "pass", "source_text_matching": "pass", "unsupported_handling": "not_applicable"}` — The first citation locates greedy decoding on PDF page 4; the continuation on page 5 explicitly leaves other decoding methods to future work. Both pages are needed and are cited.

### lim_18 / hybrid

Question: When are encoder-decoder models relatively robust to relevant-information position?
Reference: Within their training-time context length; longer evaluation sequences exhibit positional degradation.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual review (assistant, Codex): `{"answer_correct": "fail", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "not_applicable"}` — No answer was returned: generation_failed. This is a failed service outcome, not an abstention or an invented incorrect answer. No citations or contexts were preserved for this failed generation, so evidence/page/text checks are not applicable.

### lim_18 / semantic

Question: When are encoder-decoder models relatively robust to relevant-information position?
Reference: Within their training-time context length; longer evaluation sequences exhibit positional degradation.
Answer: Unavailable: generation_failed
- faithfulness: error (generation_failed)
- answer_relevancy: error (generation_failed)
- context_precision: error (generation_failed)
- context_recall: error (generation_failed)
- factual_correctness: error (generation_failed)
Deterministic checks: `{"answerability_correct": null, "citation_identity_and_scope": null, "citations_present_when_answered": null, "expected_page_coverage": null, "quote_in_context": null}`
**Flagged:** execution or deterministic source/abstention check requires attention.
Manual review (assistant, Codex): `{"answer_correct": "fail", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "not_applicable"}` — No answer was returned: generation_failed. This is a failed service outcome, not an abstention or an invented incorrect answer. No citations or contexts were preserved for this failed generation, so evidence/page/text checks are not applicable.

### lim_19 / hybrid

Question: What vision-backbone training schedule does this paper prescribe?
Reference: Not applicable: unsupported question; expected abstention.
Answer: I couldn’t find enough evidence in this document to answer that question.
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 3888.481166002748, "temperature": null}`
Answer-chain latency: 3300.4 ms; shared retrieval: 3888.5 ms.
Retrieved chunk IDs: a6d810c170ed501b259df2c1d28c5fca5bf45658e92601ba8a83682d0cba543a, e28061d534284a899a7d6723ba114fc17a03a9704a42ca3e2902e6bfef5822b2, 44ce30adbb0f79c9b399d10b094449d355f65bc9a95b6f8b5eab6a13d0708b07, 3d226376378c7ff78047e1fb53a6d3aa0f9e5feda44e98390359a00e111eab51, 8db234810fe5cc92665f500c3b4245d828f87073d5cbc319649791fd25c40cff, a4169151d03ceb16c0b0c67f263ef198d8d018c61b9c427d13023f666a27f963; source pages: \[\[8\], \[8, 9\], \[5\], \[9\], \[2\], \[14, 15\]\].
- faithfulness: skipped (unanswerable_case_use_guardrail_review)
- answer_relevancy: skipped (unanswerable_case_use_guardrail_review)
- context_precision: skipped (unanswerable_case_use_guardrail_review)
- context_recall: skipped (unanswerable_case_use_guardrail_review)
- factual_correctness: skipped (unanswerable_case_use_guardrail_review)
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": null, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "pass"}` — The system explicitly abstains with no fabricated citations. The paper studies long-context information use; it prescribes no vision-backbone training schedule.

### lim_19 / semantic

Question: What vision-backbone training schedule does this paper prescribe?
Reference: Not applicable: unsupported question; expected abstention.
Answer: I couldn’t find enough evidence in this document to answer that question.
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 3888.481166002748, "temperature": null}`
Answer-chain latency: 2027.1 ms; shared retrieval: 3888.5 ms.
Retrieved chunk IDs: a4169151d03ceb16c0b0c67f263ef198d8d018c61b9c427d13023f666a27f963, 7dd547dad735f2ea349a3da74e15632879934b493ea1e314f97023c49aab0195, 12cd655523936f95ed1f9d8803e7e4c95d26db6d3c0bb9bf4a2a72f2265c2c7b, a6d810c170ed501b259df2c1d28c5fca5bf45658e92601ba8a83682d0cba543a, 25fb15fafa1ce428d56fa71f1b69a87c07801c5a25ac54997bededd04430c797, e28061d534284a899a7d6723ba114fc17a03a9704a42ca3e2902e6bfef5822b2; source pages: \[\[14, 15\], \[13\], \[9, 10\], \[8\], \[12\], \[8, 9\]\].
- faithfulness: skipped (unanswerable_case_use_guardrail_review)
- answer_relevancy: skipped (unanswerable_case_use_guardrail_review)
- context_precision: skipped (unanswerable_case_use_guardrail_review)
- context_recall: skipped (unanswerable_case_use_guardrail_review)
- factual_correctness: skipped (unanswerable_case_use_guardrail_review)
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": null, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "pass"}` — The system explicitly abstains with no fabricated citations. The paper studies long-context information use; it prescribes no vision-backbone training schedule.

### lim_20 / hybrid

Question: What GPU operating temperature was measured during the experiments?
Reference: Not applicable: unsupported question; expected abstention.
Answer: I couldn’t find enough evidence in this document to answer that question.
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "hybrid", "rrf_constant": 60, "shared_retrieval_ms": 3001.4207090061973, "temperature": null}`
Answer-chain latency: 1964.0 ms; shared retrieval: 3001.4 ms.
Retrieved chunk IDs: 91ead4a79e08e8aa5ae66ae2bf9c32cecf2de6c653c02ec54a11d189e0730e96, b28f5492d56c4103e45c7048b03c9eb264914a6dc5ab054da6e86ab0dcbe0b8d, 66940e5044b883564f960e5645f6d4fa9ca0f4155dfad86f90edd9644fcddf30, 01898750abc58013db5cedbaac74d4d7a1925ce7aafc592342138a64979b1939, 9047ccb2f95eb1604a89fc59445d41f3b0f745c2136268b52e2895929273b4d7, fb0421f20e7333b9f9d470d7aa85c5e88f3d70e704cd3d2caad8ed00c6f8a898; source pages: \[\[5\], \[15\], \[1, 2\], \[5\], \[8\], \[15\]\].
- faithfulness: skipped (unanswerable_case_use_guardrail_review)
- answer_relevancy: skipped (unanswerable_case_use_guardrail_review)
- context_precision: skipped (unanswerable_case_use_guardrail_review)
- context_recall: skipped (unanswerable_case_use_guardrail_review)
- factual_correctness: skipped (unanswerable_case_use_guardrail_review)
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": null, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "pass"}` — The system explicitly abstains with no fabricated citations. The paper reports no measured GPU operating temperature.

### lim_20 / semantic

Question: What GPU operating temperature was measured during the experiments?
Reference: Not applicable: unsupported question; expected abstention.
Answer: I couldn’t find enough evidence in this document to answer that question.
Pipeline configuration: `{"candidate_k": 20, "chunk_overlap": 150, "chunk_set_id": "475b200ffbe27b4593df703ccc55030a3eba38c7d26ecef31c8c2291301d0bd5", "chunk_size": 1200, "context_bytes": 32000, "context_k": 6, "dimensions": 1024, "embedding_model": "voyage-4-lite", "embedding_profile_id": "cd617356fdb2672b5289bb19ebd45e5243a43fe93766c1675a284871f9635536", "evaluation_history": "single_turn_no_chat_storage", "model": "openai/gpt-5.6-luna", "pipeline_version": "hybrid-rag-v1", "retrieval": "semantic", "rrf_constant": 60, "shared_retrieval_ms": 3001.4207090061973, "temperature": null}`
Answer-chain latency: 2270.0 ms; shared retrieval: 3001.4 ms.
Retrieved chunk IDs: 91ead4a79e08e8aa5ae66ae2bf9c32cecf2de6c653c02ec54a11d189e0730e96, 01898750abc58013db5cedbaac74d4d7a1925ce7aafc592342138a64979b1939, 9047ccb2f95eb1604a89fc59445d41f3b0f745c2136268b52e2895929273b4d7, fa004736522339d55cc025d823b9440090a58a7768dd9d5f141f04ed7554e506, dc9a307c4195bde2e1be3d3815ea36839caa039d3112e28c7a1f98ca314c8a40, 735f9a7a53bc23596ec61356477a2311a34af134df6b7f7c03a30c4cbbb14c44; source pages: \[\[5\], \[5\], \[8\], \[5\], \[8\], \[10\]\].
- faithfulness: skipped (unanswerable_case_use_guardrail_review)
- answer_relevancy: skipped (unanswerable_case_use_guardrail_review)
- context_precision: skipped (unanswerable_case_use_guardrail_review)
- context_recall: skipped (unanswerable_case_use_guardrail_review)
- factual_correctness: skipped (unanswerable_case_use_guardrail_review)
Deterministic checks: `{"answerability_correct": true, "citation_identity_and_scope": true, "citations_present_when_answered": true, "expected_page_coverage": null, "quote_in_context": true}`
Manual review (assistant, Codex): `{"answer_correct": "pass", "citation_pages": "not_applicable", "evidence_support": "not_applicable", "source_text_matching": "not_applicable", "unsupported_handling": "pass"}` — The system explicitly abstains with no fabricated citations. The paper reports no measured GPU operating temperature.

## Limitations

This is one paper and one model/pipeline configuration. LLM judges can vary or be wrong. Page coverage is a coarse deterministic diagnostic, not Ragas context recall. Reference approval and generated-answer review are separate. Assistant reviews are not independent human validation. See the JSON artifact for complete contexts and citations; do not publish private-paper runs.
