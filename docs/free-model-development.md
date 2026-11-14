# Free-model development setup — 14 November 2026

The user-supplied replacement OpenRouter key was verified and saved only in the ignored local `.env` with mode 0600. No key is included in these docs. The API and workers were gracefully restarted while no jobs were active.

During this free-model trial, local model roles used `nvidia/nemotron-3.5-super-vl:free`; `EVAL_JUDGE_MODEL` explicitly selects the same free model for any future manually requested evaluation. Full Ragas was not run. LlamaParse and Voyage configuration were preserved and remain separate providers.

## Confirmed results and limitation

- Both real summary/chat JSON schemas returned HTTP 200 and passed schema validation.
- The actual 11-page `EJ1172284.pdf` retry reused the stored parsing. Current chunk/embedding records were refreshed for the existing v2 chunker (63 chunks).
- With provider-default thinking, a real summary response used all 4,096 completion tokens for reasoning, returned `finish_reason=length`, and had no finished summary. The request cost was $0.
- With thinking disabled, the response completed with 2,544 output tokens and zero reasoning tokens, also at $0. Strict source validation rejected inaccurate quote references. Repeated full-paper jobs remained FAILED. The optional setting fixes output-budget exhaustion; it does not establish full-paper answer quality.
- A bounded Ling 3.2 Flash comparison also failed exact quote checks after one correction. Baidu's tested request failed before a valid summary response. Neither alternative was selected for the application.
- Consequently, this paper is **not Ready**, and no passing full-workflow or Ragas result is claimed. The browser verification script was prepared but not run because a valid summary was unavailable. No paid-model request was made during recovery.

## Optional reasoning setting

`LLM_REASONING_ENABLED=false` sends `reasoning: {enabled: false}` through the existing completion client and offline judge. Strict JSON schema, source/page/quote checks, output limits and bounded retries remain intact. Omit the setting to retain prior defaults: GPT-5 models use low effort, other providers use their defaults. Explicit `true` enables supported non-GPT reasoning; unsupported providers may reject it.

An explicit reasoning policy participates in summary profile identity and chat evaluation traces. Existing profile hashes are unchanged when the setting is omitted. Previously generated summaries are retained; changing model/policy can make them unavailable under the current profile until regenerated. User papers other than the selected failed paper were not rescheduled.

Verification: **486 backend tests passed, 4 live-provider tests deselected**, including real disposable MongoDB/RabbitMQ integration boundaries. Focused provider/workflow/quote/evaluator tests: **58 passed**. Ruff passed. Two existing dependency deprecation warnings remain. Frontend code was unchanged by this follow-up. The 13 original unrelated local files remained outside the patch.

Private request diagnostics and test logs are at `/private/tmp/researchai-free-recovery-20261114`. The disposable regression MongoDB container was removed after tests. The normal frontend, API and workers remain running. Publication is for feature-branch review; these deterministic checks do not establish full-paper readiness.

After this trial, the primary model was restored to `openai/gpt-5.6-luna` using a replacement key in the ignored `.env`. The temporary reasoning override was removed, returning GPT-5 to low effort. The API and idle workers were restarted; authentication and health checks passed without a paid generation request. The selected paper has not yet completed a successful paid-model retest. Retry it through the supported processing API/UI when that retest is requested. Readiness still depends on successful source validation. Run Ragas separately after the selected model's workflow passes; old evaluation scores do not validate a new model.

References: [OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs), [reasoning controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens), [NVIDIA free endpoint](https://openrouter.ai/nvidia/nemotron-3.5-super-vl:free).
