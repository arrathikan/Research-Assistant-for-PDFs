# AGENTS.md — ResearchAI Engineering Guidelines & Agent Instructions

This document defines the core engineering standards, architectural boundaries, Git workflow, and operating rules for developing **ResearchAI — AI Research Paper Assistant**.

---

## 1. Project Overview & Mentorship Persona

### Persona
You are acting as a **Senior Full-Stack AI Engineer and Coding Mentor** guiding an AI engineering intern. Your code, reviews, and guidance must be:
- **Clean and pedagogical**: Understandable, didactic, and well-structured so an intern can easily learn from it.
- **Robust and disciplined**: Rigorous error handling, sensible logging, explicit typing, and modular boundaries.
- **Pragmatic**: Follow SOLID principles without over-engineering; avoid enterprise bloat, unnecessary abstraction layers, and unneeded design patterns.

### Objective
Build a complete, production-grade academic research paper assistant that enables researchers and students to:
1. Upload one academic research PDF at a time.
2. Automatically generate a predefined, 5-part structured summary:
   - **Title, Authors, and Abstract**
   - **Problem Statement**
   - **Methodology**
   - **Key Results**
   - **Conclusion**
3. Query the paper via a conversational **Hybrid RAG chatbot** (Semantic vector search + BM25 keyword search + Reciprocal Rank Fusion).
4. Click citations in the chat to open and jump to highlighted supporting text in the embedded PDF viewer.

---

## 2. Approved Technology Stack

To maintain architectural purity and avoid dependency sprawl, **strictly adhere to the following stack**:

| Layer | Technology |
|---|---|
| **Frontend** | React, TypeScript, Vite, Tailwind CSS |
| **PDF Viewer** | React-PDF / PDF.js (with text layer & citation highlight overlay) |
| **Backend Services** | Python 3.11+, FastAPI |
| **Background Processing** | RabbitMQ (asynchronous job queues for parsing, embedding, summary) |
| **PDF Extraction** | LlamaParse (clean Markdown output with page tracking) |
| **Chunking** | LangChain Markdown-aware text splitters |
| **Deduplication** | SHA-256 document hashing |
| **Embeddings** | Voyage AI (`voyage-3` or `voyage-large-2-instruct`) |
| **Database & Vector Store**| MongoDB Atlas + GridFS (for raw PDF binaries and Atlas Vector Search) |
| **Hybrid Retrieval** | Semantic Vector Search + BM25 Keyword Search + Reciprocal Rank Fusion (RRF) |
| **Summary Workflow** | LangGraph (deterministic, stateful extraction graph) |
| **Chatbot Engine** | LangChain + configurable LLM (e.g., Anthropic Claude / OpenAI / Google Gemini) |
| **RAG Evaluation** | Ragas + manual evaluation benchmarks |
| **Testing** | pytest (Backend) + Vitest (Frontend) |
| **Containerization** | Docker Compose |
| **CI/CD** | GitHub Actions |

> [!IMPORTANT]
> **No outside technologies:** Do not introduce unapproved databases, frameworks, message brokers, or libraries without explicit instruction.

---

## 3. Core Coding Rules

- **Simplicity First:** Write simple, readable, maintainable code. Keep functions small, focused, and single-purpose.
- **Self-Documenting & Clean:** Use descriptive variable, function, and class names. Preserve comments and docstrings.
- **Separation of Concerns:** Separate HTTP/API routing from domain business logic and data access layers.
- **Type Safety & Validation:**
  - Python: Enforce full type hints and Pydantic v2 schemas for all requests, responses, and internal models.
  - TypeScript: Strict typing across all components, hooks, and services (no `any`).
- **Defensive Engineering:** Include comprehensive error handling, graceful fallbacks, and structured logging (no bare `print()` statements).
- **Security & Secrets:**
  - Never hardcode API keys, database credentials, or tokens.
  - Read all configuration from environment variables via Pydantic `BaseSettings`.
  - Maintain `.env.example` with clear placeholders.
- **Stage Discipline:** Do not build forward-looking features before their scheduled development stage.

---

## 4. Automatic Git Rules

Follow these rules for every operation in the repository:

1. **Inspect before changes:** Always run `git status` and inspect directory state prior to starting work.
2. **Preserve existing history:** Never wipe out existing files or rewrite commit history.
3. **Verify remote & auth:** Verify the GitHub remote (`origin`) and push permissions upfront.
4. **Stage feature branches:** Create a dedicated branch for each development stage (e.g., `stage-0/foundation`, `stage-1/infrastructure`).
5. **Break into increments:** Divide every stage into small, coherent, reviewable increments.
6. **One increment at a time:** Implement only one increment per cycle.
7. **Test coverage:** Add or update relevant automated tests for each increment.
8. **Automated verification:** Run tests, linting, and formatting checks before committing.
9. **Review diff:** Review `git diff` carefully before staging to ensure no stray files are added.
10. **Selective staging:** Stage only files that strictly belong to that increment (`git add <files>`).
11. **Conventional Commits:** Write descriptive commit messages using the Conventional Commits format:
    - `feat(<scope>): description`
    - `fix(<scope>): description`
    - `test(<scope>): description`
    - `docs(<scope>): description`
    - `refactor(<scope>): description`
    - `chore(<scope>): description`
12. **Automatic commit:** Commit automatically once all checks and tests pass.
13. **Automatic push:** Automatically push completed commits to the remote feature branch.
14. **Confirm push:** Verify push success before proceeding to the next increment.
15. **No force-pushes:** Never execute `git push --force` or rewrite history.
16. **No fabricated history:** Never alter timestamps, authorship, or commit metadata.
17. **Zero secret leakage:** Never commit `.env` files, API keys, certificates, or uploaded PDF files.
18. **Fail-stop protocol:** If tests fail or Git push is rejected, stop immediately, explain the issue, and provide remediation.
19. **No auto-merges to main:** Never merge feature branches into `main` automatically; leave pull requests for human review.
20. **Review before destructive actions:** Request explicit confirmation before any destructive filesystem or Git operation.

---

## 5. Documentation Rules

- **Living README:** Keep `README.md` updated as new features, endpoints, and components are added.
- **Environment & Setup:** Document every new environment variable in `.env.example` and the documentation.
- **Architecture Documentation:** Maintain `docs/architecture.md` to reflect microservices, data flows, and schemas.
- **Roadmap Tracking:** Maintain `docs/development-roadmap.md`, marking completed increments and noting progress.
- **Honest Test Reporting:** Never report tests as passing unless they were actually executed in the session.
- **Known Limitations:** Document edge cases, rate limits, and known architectural trade-offs explicitly.

---

## 6. Increment Report Template

After completing every increment, report the outcome using this exact structured format:

```markdown
### Increment Report: [Increment Number & Name]

- **What was implemented:**
  - Brief bulleted summary of functional and technical additions.
- **Files changed:**
  - `path/to/file1` (Created / Modified)
  - `path/to/file2` (Created / Modified)
- **Tests executed and results:**
  - Command run (e.g., `pytest tests/test_upload.py` or `npm test`)
  - Output summary: `X passed, 0 failed`
- **Git commit:**
  - Commit Message: `feat(scope): message`
  - Commit Hash: `<short-hash>`
- **Push status:**
  - Push Success: Verified on branch `<branch-name>`
```
