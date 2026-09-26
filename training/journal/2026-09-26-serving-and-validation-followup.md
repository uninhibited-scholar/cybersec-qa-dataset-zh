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
