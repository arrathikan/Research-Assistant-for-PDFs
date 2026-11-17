# ResearchAI — Quality Assurance & Verification Report

**Verification Date:** November 13, 2026
**Project:** ResearchAI — AI-Powered Research Paper Assistant
**Status:** Development verification completed; production hardening required

**Historical scope:** The results below describe November 13. The [later live QA report](live-e2e-qa-2026-11-14.md) records additional source-validation failures and blocked retests. Earlier passing results do not establish that a later revision or a fresh paper passed the same checks.

## 1. Executive Summary

ResearchAI underwent functional, integration, browser, and containerized verification to evaluate system reliability, AI workflow behavior, and readiness for technical demonstration.

The verification covered:

- Backend API and document-processing services
- MongoDB Atlas and RabbitMQ integration
- LangGraph-based research paper summarization
- Hybrid RAG retrieval and citation validation
- React frontend and interactive PDF viewer
- Docker Compose deployment
- Offline Ragas evaluation
- Dependency and security checks

The verified public-paper workflow completed successfully after resolving a summary citation-validation issue.

**Overall assessment:** The application demonstrated working end-to-end functionality under the tested conditions. However, answer-quality limitations, dependency vulnerabilities, and missing production security controls remain unresolved.

---

## 2. Verification Summary

| Verification Area | Result | Status |
|---|---|---|
| Backend test suite | 474 passed; 4 paid checks excluded | Passed |
| Summary regression tests | 21 passed | Passed |
| Frontend Vitest (committed source) | 140 passed across 19 files | Passed |
| TypeScript validation and build | Completed successfully | Passed |
| Chromium browser tests | 14 passed | Passed |
| Live browser integration | 1 passed | Passed |
| Docker full-stack smoke test | Completed successfully | Passed |
| Python lint and formatting | Passed | Passed |
| Ragas evaluation | 18 responses; partial metric coverage | Completed with issues |
| Dependency audit | 10 security findings | Action required |

The local frontend workspace also passed 144 tests across 20 files, including four tests not included in the committed source-equivalent verification.

Test results represent the specified verification environment and are not a guarantee of correctness under all production conditions.

---

## 3. Resolved Issue: Summary Source Validation

### Problem

During live verification, a processed research paper contained:

- Completed LlamaParse extraction
- 105 Markdown-aware document chunks
- Voyage AI embeddings
- An unsuccessful structured-summary job

The summary workflow repeatedly failed because the language model returned source quotations containing inserted ellipses.

ResearchAI's strict validation correctly rejected the quotations because they did not match contiguous source text.

### Resolution

The summarization workflow was refined to:

1. Request shorter, contiguous, verbatim quotations.
2. Provide clearer feedback during bounded correction attempts.
3. Preserve strict chunk, page, and source-quote validation.
4. Update the workflow version to distinguish revised summary artifacts.

The existing validation rules were not weakened.

### Verified Outcome

After the correction, a supported processing retry completed successfully on its first job attempt.

The resulting summary contained:

- Seven completed summary fields
- Thirteen verified source records
- Successful validation against current document chunks
- Reuse of previously generated extraction and embedding artifacts

The original source PDF identity was verified without unnecessarily repeating paid document processing.

---

## 4. Backend and Integration Testing

The backend test suite completed with **474 passing tests and four optional paid-provider checks excluded**.

Testing covered:

- API request validation and response contracts
- PDF upload and duplicate detection
- MongoDB and GridFS persistence
- RabbitMQ processing and recovery behavior
- LangGraph summarization
- Embedding and retrieval interfaces
- Citation and source validation
- Document lifecycle operations
- Evaluation schemas and reporting

Integration checks used disposable MongoDB and RabbitMQ resources, with deterministic substitutes for paid AI providers where applicable.

The verification also included 21 focused summary regression tests and 25 evaluation/report regression tests, both included in the full backend count.

---

## 5. Frontend and Browser Verification

The frontend underwent unit, type-checking, build, and browser-level verification.

### Test Results

| Test | Result |
|---|---|
| Frontend unit tests | 140 passed |
| TypeScript validation | Passed |
| Production build | Passed |
| Deterministic Chromium tests | 14 passed |
| Live browser integration | 1 passed |

### Functional Coverage

Browser testing verified:

- Document upload and duplicate handling
- Research dashboard interactions
- Structured summary presentation
- Chatbot responses and source navigation
- PDF page navigation and highlighting
- Responsive workspace layout
- Document deletion and cancellation
- Upload retry and repeated file selection
- Preservation of chat and viewer state

The deterministic browser suite used synthetic API responses and PDF fixtures. The separate live browser test exercised real application integrations.

### Responsive Design

The browser matrix covered viewport widths of:

`375px, 768px, 1024px, 1280px, 1440px, 1920px`

The tested layouts preserved readable content, PDF split-view behavior, and mobile navigation without observed root-level horizontal overflow.

The PDF workspace also retained conversation state, document content, page position, and zoom during supported viewer interactions.

**Testing limitation:** Safari, Firefox, physical mobile devices, and dedicated screen-reader testing were not included in this verification.

---

## 6. Docker and CI Verification

The application was tested using rebuilt Docker Compose services.

The smoke test covered:

- Frontend delivery through Nginx
- FastAPI gateway availability
- RabbitMQ and worker connectivity
- PDF upload and duplicate detection
- MongoDB GridFS storage
- Document status retrieval
- Document deletion
- Required frontend assets

Test resources were isolated and cleaned after verification.

### GitHub Actions

The CI workflow successfully completed backend, frontend/browser, and Docker full-stack smoke verification.

**Verified CI run:** [GitHub Actions Run #43383787551](https://github.com/arrathikan/Research-Assistant-for-PDFs/actions/runs/43383787551)

**Verified code commit:** `81064f5`

The CI environment used Python 3.12 and Node.js 22.

Standard CI did not require paid AI provider calls.

---

## 7. RAG Evaluation Results

ResearchAI's RAG evaluation uses Ragas with automated scoring and source-based reviews.

The final QA evaluation included nine research-assistant questions tested across two retrieval strategies.

### Results

| Measurement | Result |
|---|---:|
| Evaluation questions | 9 |
| Generated responses | 18 |
| Recorded Ragas metric values | 58 |
| Applicable metric skips | 30 |
| Metric errors | 2 |
| Assistant-reviewed responses | 18 |

The evaluation measured applicable aspects of:

- Faithfulness
- Answer Relevancy
- Context Precision
- Context Recall
- Factual Correctness

### Identified Quality Issues

The evaluation identified:

- Seven answers with incomplete inline claim support
- Three answers with additional attribution or answer-quality issues
- Two context-recall metric errors involving overview responses
- Cases where broad summary claims did not cite all relevant evidence

The unavailable metric values were preserved as errors rather than replaced with fabricated scores.

Reviews were assistant-generated and were not represented as independent human approval.

**Interpretation:** The results establish that the evaluation process executed and exposed real quality issues. They do not demonstrate universal scientific-answer accuracy or consistent superiority of hybrid retrieval.

Full results are available in the [Ragas Evaluation Report](../evaluation/reports/2026-11-13-final-qa/README.md).

---

## 8. Security and Dependency Review

The dependency audit reported **10 findings**:

| Severity | Findings |
|---|---:|
| Critical | 3 |
| High | 5 |
| Moderate | 2 |
| **Total** | **10** |

The identified dependency chains involve components including React-PDF, PDF.js, canvas, tar, Vite, Vitest, esbuild, and tinypool.

The PDF viewer uses the documented `isEvalSupported: false` mitigation relevant to a PDF.js advisory. This does not resolve the underlying dependency vulnerabilities.

Affected packages require compatible upgrades and regression testing before public production deployment.

### Additional Security Limitations

The current deployment does not provide a complete production security configuration, including:

- User authentication
- Per-user authorization
- Public TLS termination
- Comprehensive production monitoring and alerting

Development servers should remain restricted to trusted local environments.

---

## 9. Known Limitations

The verification identified several areas requiring further work.

| Area | Limitation |
|---|---|
| AI summarization | Provider responses may fail strict source validation |
| Citation reliability | Some generated claims lack complete citation support |
| RAG evaluation | Limited benchmark size and partial metric coverage |
| Dependencies | Unresolved security advisories |
| Authentication | No complete user-account and authorization system |
| Deployment | Additional production hardening required |
| Browser compatibility | Safari and Firefox not verified |
| Accessibility | Dedicated screen-reader verification not performed |
| Document library | Session-oriented state has persistence limitations |
| Health monitoring | Basic API health does not confirm all external dependencies |

These limitations do not invalidate the verified tests, but they restrict the conclusions that can be drawn from them.

---

## 10. Recommended Next Steps

Before considering public production deployment, the following improvements are recommended:

1. Resolve high- and critical-severity dependency advisories.
2. Implement authentication and document-level access control.
3. Improve citation completeness and answer attribution.
4. Expand Ragas benchmarks across additional research domains.
5. Add comprehensive cross-browser and accessibility testing.
6. Introduce production monitoring and dependency-readiness checks.
7. Perform a complete security and deployment review.

---

## 11. Supporting Documentation

- [System Architecture](architecture.md)
- [Browser QA](browser-qa.md)
- [Deployment Guide](deployment.md)
- [CI Verification](ci.md)
- [Structured Summarization](structured-summary.md)
- [RAG Evaluation](rag-evaluation.md)
- [Detailed Evaluation Results](../evaluation/reports/2026-11-13-final-qa/README.md)
- [Demo Guide](demo-guide.md)

---

## Conclusion

ResearchAI successfully completed the documented backend, frontend, integration, browser, and containerized verification checks.

The final QA also demonstrated recovery from a real summary-generation failure without weakening evidence-validation requirements.

The project is suitable for presenting its verified engineering workflows in a technical demonstration. Additional improvements in answer quality, dependency security, and operational controls are necessary before public production deployment.

**Verification scope:** November 13, 2026. Results reflect the tested configurations and documented conditions, not a general certification of production readiness.
