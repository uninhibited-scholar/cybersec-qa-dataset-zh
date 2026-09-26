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
Corrected-r2 was still generating at inspection time (14 detail records;
aggregate result not yet written). This exposed-set diagnostic is not a blind
capability score and is not promotion evidence.

## Scope and next action

No production API, production adapter, evaluation data, rubric, permissions,
or candidate weights were modified. Wait for `44624` to finish and verify its
final aggregate and hashes. Continue `44617` fixed validation only when the
scheduler allocates it; do not treat validation loss or the separate Qwen14B
API smoke as proof that Phase108 is deployable.
