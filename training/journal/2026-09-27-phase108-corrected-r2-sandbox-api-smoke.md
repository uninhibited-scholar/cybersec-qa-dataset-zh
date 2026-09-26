# Phase108 corrected-r2 isolated API smoke

Date: 2026-09-27 (HKT)

## Scope

Validated the corrected-r2 adapter through an isolated, loopback-only API on a
CUHK GPU-MEDIUM node. This is serving/loader compatibility evidence only; it is
not a capability score, blind evaluation, deployment approval, or production
change.

## Reproducibility and provenance

- Slurm job: `44763`; state `COMPLETED`, exit `0:0`, elapsed `00:00:56`.
- Node/runtime: `dell3090`, NVIDIA GeForce RTX 3090, BF16, compute capability
  `[8, 6]`.
- Adapter:
  `models/phase108-cuda-recovery-scale20-corrected-20260924-r2/adapters.safetensors`
  SHA-256 `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`.
- Base config SHA-256:
  `260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650`.
- Base shard-index SHA-256:
  `5e699a61da09415f33a625885364d3889a80acb6ab88aedaf6e195b2612addf4`.
- Scale: `20.0`; server reported 28 adapter projections loaded.
- SBATCH script SHA-256:
  `75821f588a34899c2756499c806cc18208ec965244216130deb0c1407d3fd42a`.
- Server SHA-256:
  `df1484bd0b01ee72e3b41dbb2a7ceda7b384d1e08f99239ffde68357338f83f7`.
- Loader SHA-256:
  `00ef5d3b1aaada8285b711a68f47c9e00a4fb9dbbd993e8eaf8eefd7426fa371`.
- Smoke client SHA-256:
  `b1ac9d684a3e0efa3d445fe67c779fd1fafa73fcc62cc9944a44fcd511b909b2`.
- Aggregate result SHA-256:
  `2c8bcd925b5e03ff68d3dbbaa56b1c57231c6aeb889ca180eb68838419ac48c1`.

## Outcome

- Health and model discovery: HTTP 200; model ID `phase108-candidate`.
- One benign chat-completion check: HTTP 200, non-empty (54 characters),
  `finish_reason=stop`, 4.516 s end-to-end.
- Tool-request check: HTTP 400 as expected; the isolated service exposes no
  tools.
- API bound to `127.0.0.1` only and was stopped by the job cleanup trap.
- Smoke summary SHA-256:
  `2c8bcd925b5e03ff68d3dbbaa56b1c57231c6aeb889ca180eb68838419ac48c1`.
- Health summary SHA-256:
  `66af92f1cdb0b41e33ae9ab5f6d9d4a2171b465c487b7fb450480dda3ae9bc2b`.

## Interpretation and invariants

This resolves the narrow question “can this exact adapter be loaded and return
non-empty text through the isolated API at the configured scale?” with a
positive result. It does not establish answer quality, cyber specialization,
general instruction following, hallucination behavior, or safety. No production
API, adapter, rubric/protocol, tool permission, candidate weight, or evaluation
data was changed. The separate Qwen3-14B service remains a generic service with
`phase108_adapter_loaded=false` and is not this candidate.

Next gate: finish/freeze the independent holdout and collection manifest, then
run the prescribed blinded regression suite. Do not promote based on this smoke.
