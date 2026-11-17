# Provider configuration

Copy `.env.example` to the ignored root `.env` and populate credentials locally.
Never place credentials in `VITE_` variables, Docker build arguments or source
control. Restart gateway and worker processes to reload cached settings.

## Completions

`LLM_PROVIDER` currently accepts only `openrouter`. `OPENROUTER_API_KEY` is an
OpenRouter credential, not an OpenAI API credential. The client calls the fixed
`https://openrouter.ai/api/v1/chat/completions` endpoint. `OPENROUTER_BASE_URL` is
not a consumed setting; adding it does not change routing.

`PRIMARY_REASONING_MODEL` selects summary and chat generation. The template's model
identifier is configuration, not a guarantee of provider availability. Check your
account's access, quota and strict JSON-schema support before a live demonstration.
`OPENROUTER_APP_URL` and `OPENROUTER_APP_NAME` supply attribution only.

`LLM_MAX_RETRIES` bounds transient transport retries. `LLM_TIMEOUT_SECONDS` and
`LLM_MAX_OUTPUT_TOKENS` bound requests. By default GPT-5 uses low reasoning effort
and omits temperature; other models use `LLM_TEMPERATURE`. Explicit
`LLM_REASONING_ENABLED=false` disables supported model reasoning to reserve output
for JSON. Omit it to preserve the existing policy. Reasoning changes participate
in relevant generation/trace profiles.

`CHEAP_REASONING_MODEL` and `VISION_MODEL` are reserved roles. They do not provide
automatic fallback or a vision pipeline. Normal requests use one configured model.
`EVAL_JUDGE_MODEL` independently selects the offline judge; changing the primary
model does not automatically change the judge. Full evaluation can consume many
calls and is never part of ordinary chat or CI.

## Extraction and embeddings

`LLAMA_CLOUD_API_KEY`, `LLAMA_PARSE_TIER`, `LLAMA_PARSE_VERSION` and
`LLAMA_PARSE_TIMEOUT_SECONDS` configure LlamaParse. A fixed supported parser
version improves reproducibility; `latest` can change output.

`VOYAGE_API_KEY` authenticates directly to Voyage. The template selects
`VOYAGE_EMBEDDING_MODEL=voyage-4-lite` with `EMBEDDING_DIMENSIONS=1024`.
Supported Voyage 4 models accept 256/512/1024/2048 dimensions. Legacy supported
models require 1024. `VOYAGE_MODEL` / `VOYAGE_DIMENSIONS` and `LLM_MODEL` remain
fallback names; explicit new names take precedence. Settings without an embedding
model retain the legacy `voyage-3` default.

Changing model/dimension changes the embedding profile; regenerate compatible
vectors and ensure the Atlas index dimension matches before querying.
`VOYAGE_RERANKER_MODEL` is reserved; retrieval currently uses RRF without reranking.

## Local/demo boundaries

Template MongoDB and RabbitMQ credentials are local-only defaults. Configure an
Atlas URI, least-privilege database access and network allowlist for live hybrid
search. Ordinary local MongoDB supports storage only. See [Atlas setup](atlas-setup.md),
[search indexes](hybrid-rag.md) and [Docker runtime overrides](deployment.md).

Provider references: [OpenRouter model catalog](https://openrouter.ai/api/v1/models),
[Voyage embeddings](https://docs.voyageai.com/docs/embeddings),
[LlamaParse](https://developers.llamaindex.ai/llamaparse/).
