# Phase108 fixed-validation scale correction

Date: 2026-09-25

## Finding

An audit of Slurm job 44429 found that the fixed-validation runner installed a
rank-8 adapter with `lora_alpha=20`, giving PEFT an effective multiplier of
`20 / 8 = 2.5`. The candidate manifest records MLX direct scale 20 and PEFT
alpha 160. Therefore job 44429's loss (`2.030983971115424`) is not a valid
fixed-scale checkpoint-selection result and is withdrawn from comparison; its
validation data read itself was still restricted to the frozen 1,089-row
`valid.jsonl` (SHA-256
`44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365`).

## Artifact identity

- Candidate run: `phase108-cuda-recovery-scale20-corrected-20260924-r2`.
- No-inference provenance preflight passes with the directly verified input
  adapter SHA-256 `3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`.
- The run manifest records rank 8, MLX scale 20, PEFT alpha 160, effective
  scale 20, 19,621 training rows, and `test_split_read=false`.
- The prior blind-smoke checkpoint `0007000_adapters.safetensors` has SHA-256
  `62acbdc57011ea5a4927514c6868549d98ae36501ddbefab847424cb4ebe66ed`.
- The run's final `adapters.safetensors` has SHA-256
  `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`.
- Job 44430 tested the numbered step-7000 checkpoint at direct inference
  scale 20 and returned empty text for all 16 diagnostic prompts. This remains
  a functional failure signal, not a capability score.

## Correction and next evaluation

- Added a shared, dependency-light `mlx_scale_to_peft_alpha` helper so CUDA
  training and fixed validation use the same scale conversion.
- Fixed validation now explicitly reports requested MLX scale, rank, PEFT
  alpha, and effective scale. It keeps the same base, tokenizer, validation
  data/hash, full-row coverage, masking, maximum length, and loss definition.
- A pinned sweep covers steps 1, 1000, ..., 7000 and final weights; every
  checkpoint SHA, runner SHA, base-config SHA, input-adapter SHA, and validation
  SHA is checked before evaluation. Only the validation split is read; no
  generation outputs are emitted or stored.
- Sweep job `44517` started at `2026-09-25T23:49:58` on `dell3090` (GPU-MEDIUM).
  Its no-inference scale preflight passed. The base shard SHA-256 values
  observed inside the allocation are `model-00001-of-00002.safetensors`:
  `25094f7fbaef4769da447cb6ebf4a39d99ccc5043856cce1b4f8fc2f91ed9115` and
  `model-00002-of-00002.safetensors`:
  `a2fd70328fc4fb518bb40ac806e8c05f21ad12e228648684775f67c28104815d`.
  Result JSONL is expected at
  `results/phase108-r2-fixed-scale-validation-44517.jsonl`; the Slurm log is
  `logs/phase108-r2-valscale20-44517.log`.
- Job 44517 then failed after 1:07 before producing any validation metric:
  its loader expected `model.layers.*`, while this candidate serializes keys as
  `layers.*`. The result path exists but is empty (0 bytes) and is retained as
  a failure artifact. The base model was loaded before this key mismatch was
  noticed. The evaluator now normalizes both supported prefixes, validates
  28 A/B projection pairs and layer topology before loading the multi-GB base,
  and has unit coverage for key normalization and PEFT destination mapping.
  Corrected runner and helper hashes are pinned in a new job submission; no
  validation score from 44517 is usable.
- Corrected retry `44518` started at `2026-09-25T23:57:31` on `dell3090`.
  The normalized-key preflight passed and the base shards loaded; at the latest
  check (1:55 elapsed) it remained RUNNING with no checkpoint-level JSON metric
  written yet. Its unique output path is
  `results/phase108-r2-fixed-scale-validation-44518.jsonl`.
- At 5:02 elapsed, the first complete record (step 1) was written with adapter
  SHA-256 `7f1024dc51019a7114dfa32874b41f513161b3aff59756e59c3f49725ec22759`,
  validation loss `1.736240570593362`, 1,089 rows, effective scale 20.0, and
  train/test split access both false. The job remained RUNNING and had moved to
  the next checkpoint; no selection decision is made until all records and
  final hashes are verified.
- This correction does not change the Phase107 inference protocol or rubric.
  It corrects a training/selection-time scale mismatch. No checkpoint is
  selected from the invalid 44429 metric.
- The v0.9 private suite has already been used diagnostically and is not a
  pristine promotion holdout. A fresh independent blind suite remains required
  after candidate selection and semantic-freshness review.

## Deployment and isolation

Production API, Phase91 adapter, evaluation rubric/protocol, and tool
permissions remain unchanged. Candidates remain in the isolated sandbox.
