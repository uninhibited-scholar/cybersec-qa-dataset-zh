# Cluster API availability — 2026-09-27

## Decision correction

Serving availability and Phase108 specialist qualification are separate work
streams. The general model endpoint should have been made usable independently
instead of letting unresolved candidate evaluation delay all API access.

## Current service

- Slurm job `44601`, `qwen14b-api-service`, is `RUNNING` on `a100-3` in
  allocation `GPU-LARGE`; it started at 2026-09-26 20:45:33 HKT and expires at
  the two-day allocation limit, 2026-09-28 20:45:33 HKT.
- Primary: general `Qwen3-14B-BF16`; fallback: `Qwen3-1.7B` CPU. This service
  does **not** load a Phase108 adapter (`phase108_adapter_loaded=false`). It is
  not evidence that the cyber-specialist candidate is ready or promoted.
- Model router remains bound to node loopback (`127.0.0.1:28603`). An
  authenticated gateway is running as an overlapping Slurm step, bound only to
  compute-node private IP `172.16.5.184:49173`, allowing only source
  `172.16.5.179`. It requires a bearer token, does not log request/response
  bodies, and rejects tool/function calls.
- Local SSH forward is listening on `127.0.0.1:19002` (SSH PID `73372`):
  local port 19002 -> controller -> `172.16.5.184:49173` -> loopback router.
  API base URL for this Mac is `http://127.0.0.1:19002/v1`; model ID is
  `qwen3-14b-bf16`.
- The bearer token is stored locally, mode `0600`, at
  `/Users/zhujiehan/.config/cyber-model/qwen14b-cluster-api-token`. Never
  include its contents in Git, logs, or chat. The local forward must be
  restarted after this Mac reboots or the SSH process exits; the compute
  service/gateway end with the Slurm allocation.

## Verification

- Service smoke metadata: health/model discovery passed; both the CPU fallback
  and 14B primary returned non-empty JSON and SSE responses; route labels were
  correct.
- Authenticated end-to-end request through the Mac tunnel: `/health` 200,
  `/v1/models` 200, benign chat 200/non-empty with `X-Model-Route: big`.
- Unauthenticated `/health`: 401.
- Gateway unit tests: 5/5 passed. Gateway now forwards `X-Model-Route`, so
  fallback responses remain distinguishable from primary responses.
- Gateway SHA-256 deployed to the compute allocation:
  `0f7d4a43d33b5f36de1aafd3dc971e6a65c2faa582cf3bf52912216b560354c7`.
- No API tools are enabled. Production API/adapter, Phase108 weights, rubric,
  protocol, and permissions remain unchanged.

## Limits and next step

This provides a temporary, usable general-model API on this Mac for the
remaining Slurm allocation, not a public endpoint and not the trained
cyber-specialist API. Recheck job/tunnel health before use after reconnects.
Do not claim specialist capability until the isolated Phase108 candidate
passes its functional, fixed-validation, blind, and rollback gates.
