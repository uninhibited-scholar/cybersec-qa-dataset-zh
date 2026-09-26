# Serving priority audit — 2026-09-26

## User question

The user asked why a stable cluster API was not completed before further Phase108 evaluation. This audit records current evidence and corrects the work order; it does not authorize a production change.

## Authoritative cluster state checked

At 2026-09-26 16:49 HKT, SSH to `slurmc` succeeded. `squeue -u zj225` showed only:

- Job 44573, an unrelated user-owned pending job (`e-v32-pv`). Do not alter it.
- Job 44593, Phase108 frozen validation, pending in `GPU-LARGE` (Priority), estimated start 2026-09-28 07:14 HKT. This is a validation job, not a service.

The `/data3` quota was 280G / 479G. `Qwen3-14B-BF16` and `Qwen3-1.7B` model directories exist. The login-node MOTD prohibits running jobs on the controller and requires Slurm compute allocations.

## Serving evidence

- Job 44513 (`qwen14b-dual-api`, 30-minute smoke) is recorded by Slurm as `CANCELLED by 27818`, elapsed `00:00:00`; it never acquired a compute node and produced no runtime evidence. The audit does not infer who initiated the cancellation from the numeric UID.
- Jobs 44586 and 44589 ran isolated, loopback-only API functional checks and ended with their Slurm allocations. They were short-lived diagnostics, not a persistent endpoint.
- No cluster service endpoint or SSH tunnel has been established. Port 18765 / Phase91 production API and adapter were not changed.
- Phase108 candidate APIs and public replays were likewise ephemeral. The exposed v0.9 replay at scale 20 had severe empty-output counts, so that candidate must not be represented as a stable usable specialist endpoint.

## Correction to work order

The previous workflow incorrectly treated completion of Phase108 candidate validation as a prerequisite to making serving infrastructure available. Those are separate workstreams. A stable, isolated API/Harness transport can be built and tested without modifying production or changing the Phase108 rubric. However, an API transport smoke does not qualify an unverified adapter as a usable cybersecurity specialist. Model identity, base/adapter pairing, runtime scale, startup/health gates, loopback binding, SSH-tunnel path, timeout/error behavior, and clear fallback labeling must all be explicit.

Next action: resume the separately authorized Qwen3-14B BF16 + Qwen3-1.7B fallback serving path, using a truthful Slurm job name, the required compute allocation, bounded service duration, loopback-only binds, and a user-controlled SSH tunnel. Do not create overlapping jobs to evade the cluster's maximum runtime. Keep the Phase108 candidate validation and deployment gates independent. Do not alter production API, existing production adapter, rubric, or permissions.

## Status

This is an audit and correction of process, not a claim that the API is now deployed. The API remains undeployed as a persistent service; the serving task remains open.
