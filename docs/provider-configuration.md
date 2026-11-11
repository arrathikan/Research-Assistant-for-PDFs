# Provider configuration

Copy `.env.example` to the ignored `.env` and populate credentials locally. Never
copy credentials into frontend `VITE_` variables. Existing running services must
be restarted to reload their cached settings.

The configured completion gateway is OpenRouter. `OPENROUTER_API_KEY` belongs only
to `https://openrouter.ai/api/v1`; do not send it to OpenAI's API or put it in
`OPENAI_API_KEY`. `OPENROUTER_APP_URL` and `OPENROUTER_APP_NAME` supply application
attribution for future completion clients. They do not rename ResearchAI's UI.
`LLM_PROVIDER` accepts only `openrouter`.

| Setting | Configured value / purpose |
| --- | --- |
| `PRIMARY_REASONING_MODEL` | `openai/gpt-5.6-luna` |
| `CHEAP_REASONING_MODEL` | `meta-llama/llama-3.3-70b-instruct` |
| `VISION_MODEL` | `mistralai/mistral-small-3.1-24b-instruct` |
| `LLM_MAX_RETRIES` | 3; validated range 0–5 |
| `OPENROUTER_APP_URL` | `https://verdeai.local` |
| `OPENROUTER_APP_NAME` | `VerdeAI` |
| `VOYAGE_EMBEDDING_MODEL` | `voyage-4-lite`; direct Voyage API |
| `EMBEDDING_DIMENSIONS` | 1024 |
| `VOYAGE_RERANKER_MODEL` | `rerank-2.5`; reserved for retrieval integration |
| `LLAMA_PARSE_TIER` | `agentic`; direct LlamaParse API |

`VOYAGE_API_KEY`, `LLAMA_CLOUD_API_KEY`, and `OPENROUTER_API_KEY` are independent
credentials. Model availability does not establish account access, quota, or
retrieval quality. Provider calls may consume credits.

For existing deployments, `VOYAGE_MODEL`, `VOYAGE_DIMENSIONS` and `LLM_MODEL`
remain fallback variable names. The new names above take precedence if both are
present. With no embedding model configured, the existing `voyage-3` default is
preserved; `.env.example` explicitly selects `voyage-4-lite`. Supported Voyage 4
models receive an explicit output dimension (256, 512, 1024 or 2048). Legacy
embedding models still require 1024 dimensions.

Changing models changes the embedding profile even when the vector dimension
stays 1024. Re-embed the document for the selected profile before searching; do
not reuse `voyage-3` vectors as though they came from `voyage-4-lite`.

The summary service now uses OpenRouter for schema-constrained completions. See
[structured summaries](structured-summary.md) for generation and verification.
Chat completion calls, automatic model fallback, vision requests and reranking
remain in their respective development stages.

Provider references: [OpenRouter model catalog](https://openrouter.ai/api/v1/models),
[Voyage embeddings](https://docs.voyageai.com/docs/embeddings), and
[Voyage rerankers](https://docs.voyageai.com/docs/reranker).
