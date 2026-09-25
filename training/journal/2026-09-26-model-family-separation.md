# Model-family choice is separate from Phase108 adapter lineage — 2026-09-26

## Decision clarification

The Phase108 adapter is trained against the Qwen3-4B Phase3-wrapper weight
space. It is not portable to a different model family. That constraint applies
to this adapter experiment only; it does not require the cluster's serving API
or Harness to use Qwen. A new serving base can be evaluated behind the stable
API/Harness contract as a separate candidate, with its own tokenizer, prompt
template, inference runtime, tool-call parser, and model-specific fine-tuning
lineage if later needed.

Do not conflate:

1. Phase108's Qwen-specific adapter training and its promotion gates.
2. Choosing a general-purpose serving model for the cluster API/Harness.
3. Harness-level improvements (context assembly, routing, tool execution,
   retries/timeouts, streaming, observability), which should be assessed as a
   separate system variable.

## Existing cross-family evidence (do not restart from a blank slate)

- Phase107 already staged GPT-OSS 20B and Gemma 4 26B on the school cluster,
  verified source/destination hashes, and completed A100 `READY` runtime
  smokes. A loopback-only OpenAI-compatible chat transport smoke also passed.
  These are operational evidence, not tool-use or task-quality proof.
- Under the frozen Phase107 v0.1 rubric/protocol, the final adjudication
  recorded 87 critical failures / 319 countable cases for Phase91 and 40 / 319
  for GPT-OSS 20B. GPT-OSS's paired scorable quality score was +0.598/8 over
  Phase91 (95% paired case-bootstrap interval +0.391 to +0.808; n=312).
- Gemma 4 had 19 critical failures / 319, but only 117/320 responses were
  scorable, with many empty or truncated responses. Its conditional quality
  score is therefore not a fair overall comparison; treat availability as a
  major runtime failure, not as a win from the critical-failure count alone.
- Phase107 was an end-to-end system comparison under a no-tool protocol. It
  does not establish that GPT-OSS is best in a live Kimi Code / DeepSeek
  Harness tool loop. Tool calls, streaming, context, timeout/retry behavior,
  and latency still need a matched Harness-specific bake-off.

## Current model-selection stance

- GPT-OSS 20B is the first non-Qwen serving candidate to re-test in the
  target Harness because it has the strongest relevant local evidence so far;
  this is a candidate priority, not a promotion decision.
- Keep Qwen3-14B as a reference/fallback if its current runtime remains
  compatible. Reuse no Phase108 adapter with it unless the base identity is
  exactly the matching Qwen checkpoint.
- Gemma 4 26B remains an optional candidate only after the empty/truncated
  output issue is diagnosed under the exact serving runtime. Do not rank it
  above GPT-OSS based on conditional metrics.
- Newer models such as Gemma 4 26B A4B or other open-weight families can be
  considered only after checking actual artifact availability, license,
  backend support, GPU memory including KV cache, and end-to-end tool behavior.
  Vendor benchmarks are hypotheses, not substitutes for our frozen tests.

## Non-change / next step

No production API, adapter, selected checkpoint, evaluation standard, tool
permission, or cluster job was modified by this clarification. The next valid
serving-model comparison is a sandboxed, identical Harness protocol with
explicit model identity, exact runtime/template versions, tool-call success,
empty/truncated rate, TTFT/tokens/s, peak GPU memory, and representative
defensive task quality. Phase108's own candidate evaluation remains separate
and must still pass its provenance, contamination, functional, blind, and
rollback gates.

## Official source links consulted for future candidates

- OpenAI gpt-oss-20b model page: https://developers.openai.com/api/docs/models/gpt-oss-20b
- OpenAI gpt-oss release/runtime notes: https://openai.com/index/introducing-gpt-oss/
- Google Gemma 4 model card: https://ai.google.dev/gemma/docs/core/model_card_4
- Mistral Small 4 release and infrastructure note: https://mistral.ai/news/mistral-small-4/
- Mistral function-calling documentation: https://docs.mistral.ai/studio/conversations/function-calling
