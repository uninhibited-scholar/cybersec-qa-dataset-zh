# Phase 70 chain audit

## Scope

Static audit only. No model training and no production service changes.

## Findings

1. `Qwen3-4B-mlx-4bit-phase3-wrapper/tokenizer_config.json` declares a
   continuation-style template that concatenates message content and has no
   role delimiters. The worker does not use that template: it manually emits
   ChatML markers (`<|im_start|>...<|im_end|>`).
2. `mlx_agent_worker.py` drops all incoming `system` messages and runtime
   context, replacing them with its own fixed system block. This is an
   intentional boundary, but it means Harness formatting instructions are
   not tested by the model route.
3. The API serializes agent requests under a process-wide `LOCK`, so requests
   are strictly sequential. A 30-second client timeout can leave the worker
   generating and produce a server-side broken pipe.
4. The generation cap is 1,400 tokens, while the client commonly requests
   700. The previous 30-second timeout is therefore an evaluation constraint,
   not evidence of an intrinsic maximum response length.
5. Evidence guards correctly short-circuit some CVE/tool cases before model
   generation. This explains near-zero elapsed times for those rows.
6. The Phase 69 adapter was trained from the base wrapper without a resume
   adapter. It cannot be expected to preserve the earlier cyber adapter's
   domain behavior while learning six formatting examples.

## Minimal isolated repair proposal

- Add a candidate-only prompt snapshot test: record the exact rendered prompt
  and assert role delimiters occur once per message.
- Run candidate A/B with the same base and adapter, warm the worker first, and
  use a bounded `max_tokens` (256 for short-answer regression; 512 for open
  questions). Record per-request elapsed time and finish reason.
- Add a neutral-answer regression as a hard gate: “法国的首都是哪里？” must
  not be converted to an evidence refusal; if the model still says “未知”,
  mark the adapter as regressed rather than rewriting the answer in a wrapper.
- Keep the production route untouched. Any tokenizer/template change belongs
  in a new candidate directory and must be followed by the existing blind
  evaluation.
