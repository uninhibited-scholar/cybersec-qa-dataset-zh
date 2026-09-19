# 2026-09-19 — Phase 107 comparison protocol audit

## Finding

The prior draft called the planned run “matched” while Phase 91's production worker has internal fallback retries, evidence/tool guards, post-processing, and no caller-controlled RNG seed. The llama.cpp reference path also has additional sampler defaults unless explicitly disabled. The runtime smoke additionally used `--reasoning off`; carrying that setting into evaluation would suppress a reference model's native reasoning capability.

## Changes

- Reframed the unapproved v0.1 draft as a shared-input, fixed-output-budget, end-to-end system comparison, not a raw-weight or exact-decoding parity claim.
- Specified native/template reasoning mode for references and documented that smoke-only `--reasoning off` must not be reused for evaluation.
- Required reference sampler defaults beyond the shared first-pass controls to be disabled or recorded; record the seed mismatch because Phase 91 has no seed override.
- Kept Phase 91's internal retries and guards enabled because the primary target is its deployed endpoint, while disclosing this asymmetry. The evaluator itself should not silently retry any arm.
- Updated the draft benchmark specification to require identical user prompts, context, effective no-tool system instruction, output ceiling, timeout/parser, and rubric while recording irreducible runtime-specific differences.

## Scope boundary

These are clarifications to unapproved protocol/specification drafts only. The scoring rubric, private prompts, production service, model weights, and tool permissions were not changed. No benchmark inference or scoring was performed. The user must still approve/freeze the rubric and protocol before private cases are sent.
