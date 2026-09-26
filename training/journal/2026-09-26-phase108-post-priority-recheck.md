# Phase108 post-priority recheck — 2026-09-26

## Live evidence

At 22:37 HKT, the CUHK Slurm controller reported:

- Corrected-r2 fixed-validation sweep `44617` was still `PENDING (Resources)`
  in `GPU-MEDIUM` (`dell3090` is mixed/occupied). Slurm's then-current
  backfill estimate was 2026-09-27 08:32 HKT. No validation output existed.
- General Qwen3-14B service allocation `44601` remained `RUNNING` on `a100-3`
  with an end time of 2026-09-28 20:45 HKT. It does not load Phase108 and is
  not evidence that the specialist candidate is served or qualified.
- Other visible GPU nodes were in mixed/allocated state; no second validation
  job was submitted, avoiding duplicate resource consumption and conflicting
  results.
- `/data3` remained at 280G / 479G (58.5%), below the 95% stop threshold.

## Candidate diagnosis retained

The current corrected-r2 candidate is not deployable. The already-exposed
matched replay reports immediate EOS at effective adapter scale 20 for both
the parent and corrected-r2, while scale 5 gives non-empty outputs but every
output reaches the 128-token cap, including the scale-zero control. These are
diagnostics on exposed cases, not capability evidence and not a basis for
choosing an inference scale.

The scale-20 validation sweep is pinned to the corrected-r2 manifest, every
numbered checkpoint hash, the 1,089-row frozen validation SHA, and a validator
that only opens `valid.jsonl`. Static review confirmed it computes completion
loss with the same tokenizer template and effective LoRA scale, but it cannot
resolve the observed generation symptom. The response-generation investigation
must therefore compare controlled base/parent/candidate behavior with matched
runtime and non-truncated output caps, while keeping exposed data explicitly
diagnostic and reserving capability claims for an independent blind suite.

No API, production adapter, candidate weight, permission, rubric, protocol, or
evaluation data was modified in this recheck. The earlier priority mistake is
acknowledged: a running general-model service is a separate operational task
and does not fulfill the Phase108 specialist-model objective.

## Next actions

1. Monitor existing job `44617`; on completion, validate result count, frozen
   validation SHA, candidate and base hashes, effective scale, and split-read
   invariants before accepting any loss comparison.
2. Use those results only for checkpoint selection. Do not promote based on
   loss or compatibility alone.
3. Diagnose the EOS/length behavior with a reproducible, matched runtime
   comparison, then create a new isolated candidate only if a specific,
   testable training or inference defect is identified.
4. Complete contamination, independent blind, format, hallucination, and
   tool-permission regression gates before any deployment proposal.
