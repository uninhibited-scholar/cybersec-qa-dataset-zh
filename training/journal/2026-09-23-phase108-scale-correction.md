# Phase108 scale-correction candidate — 2026-09-23

## Scope

This note records an isolated candidate experiment only.  It does not modify
the Phase91 production API, adapter selection, tool permissions, evaluation
rubric, or the frozen/private validation material.

## Evidence from the rejected r3 compatibility probe

- Candidate: `phase108-cuda-recovery-12000-20260921-gpumed-r3/0007000_adapters.safetensors`
- Candidate SHA-256:
  `919a9eabe4a9c2fab1c66a99d3e9265fab196c34852c2489076c6b2e6b29a2d3`
- CPU probe job `44104` completed and installed all 28 LoRA projections.
- Its immutable public-probe JSONL had SHA-256
  `ba4bc3e5d35ff2cf1c4ca472732bfb622c294e889bd908cab3b267d91cff039f`.
- The four answers were nonempty but degenerated into repeated tokens.  This
  is a compatibility/behavior failure, not a blind capability score.  The
  candidate is not eligible for blind evaluation or deployment.
- GPU public-probe job `44094` failed before producing a log/result; it is
  infrastructure evidence only.

## Root cause and correction

MLX-LM applies its configured LoRA scale directly:

`base(x) + scale * ((x @ A) @ B)`.

PEFT applies `lora_alpha / rank`.  The previous CUDA recovery runner had
`rank=8, lora_alpha=20`, hence it trained with effective scale `2.5` while
the exported native MLX adapter was served with scale `20`.  The resulting
eight-fold mismatch is consistent with the repeated-token failure.

`phase108_cuda_resume_train.py` now translates native MLX `scale=20` to PEFT
`lora_alpha=160` at rank eight, preserving effective scale 20.  The rule has
a small regression test in `test_phase108_lora_scale.py`; it passed in the
cluster `coevo` environment.

## New isolated run

- Slurm job: `44108` (`phase108-scale20`)
- Input adapter (read-only) SHA-256:
  `3ed1a85e7b021e1498332a525bfa4bb75b336a03579d526f8210f1576317036`
- Target output directory:
  `/data3/ieug25/zj225/cyber-model-migration/models/phase108-cuda-recovery-scale20-20260923`
- Data: existing `phase108-clean-v2`; its test split is present but the runner
  contains no read path for it.
- Fixed seed: `20260920`; max steps `7621`; checkpoints every `1000` steps.

Before the new candidate may be evaluated, require: completed manifest with
effective scale 20, immutable checkpoint hashes, frozen validation integrity
check, compatibility smoke, then the separate semantic-review and blind-test
gates.  No result from this run alone establishes cybersecurity capability.
