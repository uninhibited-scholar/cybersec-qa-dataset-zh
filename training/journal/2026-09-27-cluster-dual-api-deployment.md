# Cluster dual-model API deployment — 2026-09-27

## Deployment state

The bounded Slurm service job `44601` is running on `a100-3` in `GPU-LARGE`
with a two-day time limit. It serves general Qwen3-14B BF16 as the primary
backend and Qwen3-1.7B on CPU as the fallback. The Phase108 adapter is not
loaded (`phase108_adapter_loaded=false`); this deployment is deliberately
separate from the cybersecurity candidate and does not promote or modify any
production adapter.

The router remains loopback-only on the compute node (`127.0.0.1:28603`). A
source-restricted, Bearer-authenticated gateway was started on the compute
node private address `172.16.5.184:49173`, with the login/controller address
`172.16.5.179` as its only accepted source. Gateway source SHA-256 is
`0f7d4a43d33b5f36de1aafd3dc971e6a65c2faa582cf3bf52912216b560354c7`.

The laptop reaches the gateway through an SSH local forward:

```text
127.0.0.1:19002 -> login node -> 172.16.5.184:49173
```

No public listener was opened. The local API configuration and token are kept
outside Git in permission-600 Desktop files; the token is not recorded here.

## Live verification

- `/health` through the laptop tunnel: HTTP 200, both `big` and `small` true.
- `/v1/models` through the tunnel: HTTP 200, model id `qwen3-14b-bf16`.
- Unauthenticated `/health`: HTTP 401 `unauthorized`.
- Authorized non-streaming chat through the tunnel: HTTP 200, non-empty
  response, route header `big`.
- The earlier in-allocation smoke also passed both non-streaming and SSE
  paths for the primary and explicit CPU fallback; fallback responses carry
  `small_fallback` and are not presented as primary output.
- Gateway unit tests: 5/5 passed. Tool/function metadata is stripped before
  forwarding because this endpoint has no tool executor; it never claims to
  execute tools.

## Boundaries and remaining operations

This proves a usable, authenticated, loopback/tunnel-reachable dual-model API,
not cybersecurity capability or Phase108 quality. GPU allocation rotation is
not automated yet: any successor allocation must be submitted transparently
through Slurm, with a health/readiness handoff and no overlapping unauthorized
GPU use. The service will end when allocation `44601` reaches its time limit
or a backend exits; the next step is a policy-compliant handoff mechanism,
then later Phase108 adapter matching and independent evaluation.

The read-only desktop checker `check-qwen-cluster-api.sh` verifies the local
tunnel health, job `44601` state, and cluster quota in one command. It does not
submit, cancel, or renew a Slurm job. The current check reports `44601`
`RUNNING` at about 1 day 2 hours and quota 292G/479G.

## Transparent successor handoff

Added `training/scripts/submit_qwen14b_successor.sh`. Given an owned current
job ID, it performs an ownership check and submits exactly one
`qwen14b_dual_api_service.sbatch` successor with
`--dependency=afterany:<current-job-id>`. It does not cancel or renew the
current job, does not create an overlapping GPU allocation, and does not
disguise the job type. The helper passes `HANDOFF_FROM_JOB` for provenance;
the service still publishes a new readiness record and tunnel template when
the successor starts. The helper was syntax-checked and passed its local fake
`sbatch`/`squeue` test. It has not been submitted, so the current production
allocation remains unchanged. A future handoff still requires refreshing the
local SSH tunnel only after the successor's readiness record is verified.

## Final deployment-gate recheck

On 2026-09-27 the read-only checker again reported API health with both
backends available, allocation `44601 RUNNING` on `a100-3`, and quota
`292G/479G`. The gateway test suite passed 5/5 with
`PYTHONPATH=training/scripts`. Kimi Code 2.0.2 made a live request through
`cluster/qwen3-14b-bf16` and returned the expected sentinel. No new allocation
was submitted and no production adapter or Phase108 rubric was changed. The
deployment phase is operationally verified; model training/evaluation remains
a later, separate phase.

## CPU fallback allocation check

The current cluster partition inventory was checked read-only. The `test`
partition exposes only 1 CPU and 1 GB, which cannot host the selected
Qwen3-1.7B fallback. `GPU-LARGE` permits CPU requests and has 32 CPUs with
192/250 GB node memory, but no separate large-memory CPU partition was
advertised. Therefore the currently running in-allocation fallback remains
the verified path; a standalone CPU fallback should only be submitted after
the cluster policy for a no-GPU request on `GPU-LARGE` is confirmed. No such
job was submitted during this check.
