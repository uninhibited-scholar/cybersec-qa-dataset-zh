# Qwen3-14B API serving path — 2026-09-26

## Scope

This is a separate, bounded cluster serving path using the previously selected
Qwen3-14B BF16 base model and Qwen3-1.7B CPU fallback. It is a general-model
API/Harness availability test, **not** the Phase108 cybersecurity adapter and
not a candidate promotion. All listeners are loopback-only on the allocated
compute node; a local SSH tunnel is required. Production port 18765, the
existing production adapter, Phase108 weights, evaluation rubric/protocol, and
tool permissions are unchanged.

## Why this work was started

The prior API work did not provide a persistent service:

- Slurm records job 44513 (`qwen14b-dual-api`) as cancelled before start with
  `Elapsed=00:00:00`.
- Jobs 44586 and 44589 were successful short-lived functional checks; Slurm
  terminated their servers when those allocations ended.
- Phase108 job 44593 is fixed validation, not a serving job, and was pending at
  the latest check.

Serving transport and Phase108 candidate qualification are separate tracks.
The former can be brought up on its own, while no Phase108 candidate is
represented as suitable for production based on the exposed empty-output
diagnostic.

## Service design

- Primary: `/data3/ieug25/zj225/models/Qwen3-14B-BF16`, BF16 Transformers on
  one `GPU-LARGE` A100-40G.
- Fallback: `/data3/ieug25/zj225/models/Qwen3-1.7B`, CPU Transformers using the
  same compute allocation's CPU resources.
- Router: existing OpenAI-compatible dual router; primary is attempted first,
  and responses carry `X-Model-Route: big` or `small_fallback` so fallback
  output is never mislabeled as the primary.
- Slurm allocation is bounded to 48 hours, the partition's maximum. No
  overlapping job is submitted to evade that cap.
- The service job performs a fallback test before loading the primary, then
  validates primary JSON and SSE calls. Any startup/health/non-empty/routing
  failure terminates the job so GPU resources are released.
- Startup writes only model config/index hashes, job/node/port metadata and
  smoke-test aggregates. Response text is inspected in memory and is neither
  printed nor persisted.
- No cluster login-node inference. The API is reachable from the Mac only via
  an SSH tunnel to the allocated compute node; public binding is not used.

## Local checks

- `bash -n training/slurm/qwen14b_dual_api_service.sbatch`: passed.
- Python AST parse of the new smoke client and three existing server/router
  modules: passed.
- `python3 -m unittest training/scripts/test_dual_model_router.py -v`: 4/4
  passed.
- Metadata-only smoke client tested against a local mocked OpenAI/SSE endpoint:
  passed; it recorded HTTP/route/non-empty/length/timing metadata only.
- Cluster read-only check found both model directories, a complete 14B shard
  index, and the `coevo` environment with torch 2.6.0+cu124 and transformers
  4.55.2.

## Current state

The service scripts are committed and synchronized to the cluster. Remote
hashes match the local commit:

- `dual_model_api_smoke.py`:
  `d3d0d93ebfc06174792da6e578e4995584390fda8b8d92be512a771bf40af622`
- `qwen14b_dual_api_service.sbatch`:
  `65ede30f4aaac0c754c64de45c029a09856dff6c7cd1734358a5f7c7543c3955`

Remote bash syntax and Python AST checks passed. The named service job was
submitted as Slurm job `44601`, requesting one A100-40G, 12 CPUs, 64G host RAM,
and the partition maximum of 48 hours. Authoritative `squeue`/`scontrol` state
at the latest check is `PENDING (Priority)`, with no assigned node or start
time. Thus **there is still no running API endpoint and no tunnel to use**.

At that same check, disk usage was 280G/479G (58.5%); job 44593 remained a
separate pending Phase108 validation; 44573 was another user-owned pending
job; 44598 was running on `dell3090`; and A100-40G nodes had active jobs. The
next step is to monitor job 44601, then verify actual startup, non-empty
primary/fallback responses, JSON/SSE routing and the SSH tunnel before handing
out a base URL. The current service is a general Qwen base-model endpoint,
explicitly not the Phase108 specialist candidate.
