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
- This correction does not change the Phase107 inference protocol or rubric.
  It corrects a training/selection-time scale mismatch. No checkpoint is
  selected from the invalid 44429 metric.
- The v0.9 private suite has already been used diagnostically and is not a
  pristine promotion holdout. A fresh independent blind suite remains required
  after candidate selection and semantic-freshness review.

## Deployment and isolation

Production API, Phase91 adapter, evaluation rubric/protocol, and tool
permissions remain unchanged. Candidates remain in the isolated sandbox.
