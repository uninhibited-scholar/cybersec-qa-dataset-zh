# Serving and Phase108 validation follow-up — 2026-09-26

## Verified cluster serving state

At 2026-09-26 20:45 HKT, Slurm job `44601` started on `a100-3`; at the
subsequent inspection it was `RUNNING` with a 48-hour allocation. Its ready
manifest reports a loopback-only router on port `28603`, Qwen3-14B BF16 as the
primary, Qwen3-1.7B CPU as fallback, and `phase108_adapter_loaded=false`.
Recorded smoke aggregates show non-empty JSON and SSE responses on both the
fallback and primary routes. A Slurm step inside the allocation returned
`/health` status `ok` with both backends healthy and `/v1/models` listed only
`qwen3-14b-bf16`.

This proves a bounded **general Qwen serving endpoint is running inside the
cluster allocation**. It does not prove that the Phase108 cybersecurity
candidate is deployed, and it does not prove local clients can reach the API.
The documented local SSH tunnel attempt failed because SSH authentication to
compute node `a100-3` was denied. Do not expose or rebind the loopback service
to work around this; use a cluster-supported tunnel path.

## Phase108 fixed-validation failure

Job `44593` failed before inference. Its log showed a manifest assertion
failure. Comparison of the manifest with the local batch script found a
one-character typo in the pinned parent adapter SHA. The script was corrected
and committed locally as `19ad85d` (`fix: correct Phase108 parent adapter SHA
pin`). `bash -n`, a comparison against independent local SHA records, and
`git diff --check` passed. The corrected script has **not yet been synchronized
to the cluster or resubmitted**; subsequent SSH access timed out during banner
exchange. Before retrying, confirm no duplicate job and verify the remote
script hash, then submit only the planned fixed-validation job.

## Operational caution

During a read-only status check, a command accidentally invoked `sha256sum` on
candidate adapter files from the login node. It was interrupted when the SSH
session stalled. Remote termination could not be confirmed before SSH access
again timed out. No model inference or training was launched on the login node.
Do not repeat file hashing or other CPU work there; perform checks within an
allocated compute job or use already recorded artifact hashes.

## Corrected validation resubmission

The corrected batch script was copied to the distinct remote filename
`data/training/slurm/phase108_followup_fixed_validation_19ad85d.sbatch`, leaving
the original remote file untouched. Remote `bash -n` passed and the pinned
parent SHA matched the local canonical record. The single planned validation
was submitted as Slurm job `44615`; the first authoritative status check showed
`PENDING (Priority)` and `sacct` showed no execution time yet. No duplicate
Phase108 fixed-validation job was present before submission. The existing local
heartbeat was updated to monitor job `44615` and verify provenance/results;
no blind evaluation or deployment was launched.

At the next scheduler check, job `44615` remained `PENDING (Priority)` with no
allocation; `squeue --start` estimated `2026-09-28T09:05:00` (cluster-reported
time). The 2-hour A100 request is not misconfigured; the delay is scheduler
priority/resource availability. A lightweight process check after reconnect
found no `sha256sum` worker from the interrupted login-node command (the only
matching `pgrep` line was the inspection shell itself).

## Live serving state re-check

At 2026-09-26 21:43 HKT, a fresh `squeue`/`scontrol` query confirmed job
`44601` was still `RUNNING` on `a100-3` and job `44615` was still
`PENDING (Priority)`. The running job's ready manifest identifies its primary
as `qwen3-14b-bf16`, fallback as `qwen3-1.7b-cpu`, and explicitly records
`phase108_adapter_loaded=false`. From inside allocation `44601`, live
`/health` returned both backends healthy and `/v1/models` listed only
`qwen3-14b-bf16`. This is a bounded, loopback-only general Qwen endpoint, not
the Phase108 model.

The separate `p108-r2-sandbox` job `44611` completed in 1m02s. Its isolated
smoke artifacts report `/health` 200, chat 200 with non-empty output, model id
`phase108-candidate`, adapter scale 20.0, tools rejected with 400, and
`promotion_eligible=false`. This was a temporary candidate compatibility
smoke, not a persistent or user-reachable service and not a capability or
deployment approval.

Therefore, as of this check, the cluster has a running general-model API and a
previously completed Phase108 sandbox smoke, but no continuously served
Phase108 API. Do not promote or replace the generic endpoint: fixed validation
`44615` and the independent blind/regression gates remain outstanding. A
later SSH retry experienced a banner-exchange timeout; the successful live
allocation health check above is the most recent authoritative service probe.

## Private v1.1 suite source preflight

The two private source banks remain gitignored. Aggregate structural inspection
confirmed 320 rows and 40 rows in each of the eight target categories. The
packer correctly rejected the suite before creating cases or keys: 153/160
prompts in source bank A are shorter than its 60-character minimum (33
vulnerability-analysis rows and all 40 rows in each of the other three A
categories); source bank B has zero short prompts. Fact-set cardinality,
multiturn role pattern, and the category/family/artifact/decision uniqueness
check did not show violations in this inspection. The builder created no
partial output. This is a draft-quality failure, not a benchmark result; source
A is being revised and independently reviewed. No model was queried.

The independent semantic review of source A rejected all 160 rows: 160 were
underspecified and shared templated framing, despite the minimum-length fix.
Therefore source A is being replaced with case-specific scenarios rather than
accepted by length alone. Source B was structurally normalized by removing the
`messages` field from its 120 non-multiturn rows; its structural checks now
pass (40/category, required fields and IDs present, prompt minimum met), but it
still awaits independent semantic review. Neither bank is frozen and no model
has seen these cases.
