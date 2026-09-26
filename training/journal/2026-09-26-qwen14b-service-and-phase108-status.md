# Qwen3-14B service and Phase108 status — 2026-09-26

## Verified cluster state

Read-only checks from the MacBook reached the CUHK login node via the existing
SSH identity. At the time of inspection, the scheduler reported:

- `44601` `qwen14b-api-service`: `RUNNING` on `a100-3`, partition `GPU-LARGE`,
  bounded by the 2-day Slurm allocation.
- `44617` Phase108 corrected-r2 fixed-validation sweep: `PENDING (Resources)`.
- `44624` Phase108 exposed scale-5/512-token diagnostic: `RUNNING` on
  `titanv1`.
- User storage: `281G / 479G` (58.7%).

Job `44601` uses `Qwen3-14B-BF16` as the primary backend and `Qwen3-1.7B` as
the CPU fallback. Its ready manifest explicitly says `phase108_adapter_loaded`
is `false`, `tools` is empty, and the listeners bind to compute-node loopback.
Thus this is a working general-model API service, not the Phase108 cyber
adapter deployment. Its isolated fallback and primary smoke results both
reported HTTP 200 and non-empty streaming and non-streaming responses. These
smokes establish service functionality only, not model capability.

For job `44624`, base-control and parent-scale-5 each completed all 16 exposed
cases with 0 empty outputs, 15 length-capped at 512 tokens, and 1 natural stop.
Their summary SHA-256 values are `0a39b422161cfcebd1240e285a339d9735b41538ee975668109dd74e56374793`
and `6a5e8af3564d949561f1db31274ca589b4a60b247b96751e4cee8c0108427cd1`.
Corrected-r2 subsequently completed all 16 cases. Its adapter SHA-256 matches
the expected corrected-r2 artifact `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`.
The corrected-r2 scale-5 summary SHA-256 is
`195d01d0050446bafe39c74394eca8c783e24b6b69f039b4513a4e46478d1a1d`.
All three arms (base-control, parent-scale-5, corrected-r2-scale-5) completed
16/16 with 0 empty outputs, 15 `length` finishes at the 512-token cap, and 1
natural stop. The corrected-r2 run took 480.717 seconds. Across the three
summaries, the case-source SHA is
`9a4d398893034b922cc67582089642c553733c856ab2812088b398a2546fbb6b`, the
job-script SHA is `ef2a8a6f9981a59e6144ac82660232a7ea07d98d44a18664c6aa1c507c54a0b9`,
the replay-client SHA is
`f503bc795cb7ad3dee3d88bf09f7527aec06261ce43a1fb8c966a7f66c59b6f1`, and the
sandbox-server SHA is
`df1484bd0b01ee72e3b41dbb2a7ceda7b384d1e08f99239ffde68357338f83f7`.
Raw prompts and responses were not saved. This exposed-set diagnostic is not a
blind capability score and is not promotion evidence; the 15/16 length caps
also mean this run does not establish answer completeness or quality.

## Scope and next action

No production API, production adapter, evaluation data, rubric, permissions,
or candidate weights were modified. Continue `44617` fixed validation only
when the scheduler allocates it; do not treat validation loss, the scale-5
diagnostic, or the separate Qwen14B API smoke as proof that Phase108 is
deployable.

## Follow-up readiness check — 2026-09-26 23:23 HKT

The scheduler still reports `44617` as `PENDING (Resources)` with an estimated
start of 2026-09-27 08:32 HKT; all GPU-MEDIUM resources were allocated in the
observed snapshot. GPU-LARGE nodes also had active allocations, so no partition
change was made. Storage was 282G/479G (58.9%).

Local checks passed: 8 Phase108 scale/provenance/preflight unit tests,
`py_compile` for the pinned validator/preflight/scale utilities, and `bash -n`
for the pending fixed-validation wrapper. The broad repository-wide
`git diff --check` did not return promptly; only that diagnostic process was
interrupted. No files were removed or altered by the interruption. A scoped
`git diff --check` for the Phase108 validator, scale utilities, Slurm wrapper,
and this journal completed successfully.

Blind-evaluation readiness remains blocked on a fresh, independently reviewed
suite: v0.9 was exposed to model inference and the current format-coverage
audit found insufficient diversity. No capability scoring or unblinding was
performed.
