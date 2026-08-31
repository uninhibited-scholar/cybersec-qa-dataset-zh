# Phase 6 Harness live regression — 2026-08-31

Environment: DeepSeek Harness Web UI on `127.0.0.1:3080`, model selector
`Qwen Cyber Agent`, temporary Phase 6 API reached through the local tunnel.

## Result

Transport succeeded in all three turns, but semantic behavior failed all three.

1. An API 500 scenario explicitly asking for knowns, unknowns, and a minimal
   validation plan was intercepted by the no-tool-evidence gate. The returned
   canned response incorrectly claimed that the user asked it to assume tools
   had run and did not answer the question.
2. A clarification explicitly stating that no tool execution was requested was
   intercepted by the same gate and returned the identical canned response.
3. A neutral comparison of HTTP 500, 502, and 504 reached model inference and
   took about 14 seconds, but the only output was the training-format residue
   `请直接给出答案，不要解释或添加额外的分析。`; no substantive answer was given.

## Diagnosis

- The SSE/timeout repair is effective: the UI receives responses and no longer
  hangs without output.
- The evidence gate has false positives and overrides legitimate analytical
  questions, including an explicit correction from the user.
- The Phase 6 adapter or prompt formatting still produces severe template
  leakage/answer suppression on an ordinary professional question.

## Decision

Phase 6 remains prohibited from deployment. Do not treat transport success as
model-quality success. The next corrective work must narrow the evidence gate
to actual execution claims and repair training/prompt formatting before another
blind Harness evaluation.
