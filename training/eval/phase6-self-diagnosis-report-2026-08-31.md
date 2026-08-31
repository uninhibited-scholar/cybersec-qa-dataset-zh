# Phase 6 self-diagnosis evaluation — 2026-08-31

## Purpose

Give the local model its real failure records and ablation observations, then
measure whether it can propose grounded root causes, minimal fixes, regression
risks, automated acceptance criteria, and explicit unknowns.

## First attempt

The long prompt contained phrases about completed actions, tools, and results in
different sentences. The execution-evidence gate combined those unrelated words
across the entire prompt and returned the canned refusal immediately.

New finding: the repaired gate is still too broad for long technical reviews.
Its three required categories must match within one sentence or a bounded
explicit pattern, not anywhere in the full request.

## Rephrased attempt

An equivalent prompt avoided the gate. The model invoked the Harness question
tool and asked two clarifying questions, which were answered with the existing
scope and evidence. It then attempted an `exit_plan_mode` tool call, but the JSON
was truncated and displayed as raw `<tool_call>` text. The requested five-part
report was not completed.

## Content assessment

Useful:

- Correctly pointed toward the outer rule and conversation history as important
  components.
- Kept some unsupported ideas labeled as inference.
- Recognized that base-model and LoRA-only ablations argue against a completely
  broken base model.

Incorrect or unsupported:

- Invented a rule specifically triggered by the phrase “只做离线文本评审”. The
  actual first-attempt failure came from cross-sentence keyword intersection.
- Proposed a cached state-machine/default-output mechanism for history failure.
  The measured cause is full contaminated history conditioning; no cache evidence
  was supplied.
- Attributed 22–37 second latency to cold start and called that observation-backed.
  The worker is persistent, and no component timing supports this conclusion.
- Treated the 502/504 confusion mainly as a prompt-engineering possibility without
  sufficient evidence; this remains a model-quality error requiring controlled
  factual evaluation.
- Failed to deliver the requested repair risks, automated tests, pass criteria,
  and unknowns because its tool-call payload was truncated.

## Decision

The model may be used as a hypothesis generator, but not as the authority for
root-cause diagnosis or repair acceptance. Every proposal still requires an
independent code-level check and blind evaluation. Before repeating this test:

1. Replace full-prompt keyword intersection with sentence-bounded gate matching.
2. Prevent planning-only tool calls for ordinary analytical requests, or ensure
   tool-call JSON has a dedicated token budget and cannot leak as raw text.
3. Add an explicit self-diagnosis rubric that penalizes invented mechanisms and
   requires each “evidence-supported” claim to cite a supplied observation.
