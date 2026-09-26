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

## Fixed-validation target mismatch found before using the queued result

At 2026-09-26 21:49 HKT, the scheduler still showed `44615` pending on
`GPU-LARGE`, estimated start 2026-09-28 09:05. Code inspection found that the
local source corresponding to its remote script name
(`phase108_followup_fixed_validation_19ad85d.sbatch`) evaluates the
`phase108-formatmix-20260925` and `phase108-bare-canary-20260925` candidates;
it does not evaluate the scale-corrected r2 adapter. The remote script hash has
not yet been freshly checked, so treat this as a target-mismatch warning until
connectivity permits that comparison.

The exact corrected-r2 final adapter is pinned elsewhere as SHA-256
`4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`. The
existing local `phase108_corrected_r2_validation_sweep.sbatch` covers its
numbered checkpoints and final adapter, checks the frozen validation hash,
scale provenance, and candidate hashes, and does not read train/test splits.
Its local SHA-256 is `f36576bf1711121ca81de6f6ce25e2f8b49de15870de1ee4e1c41662151a62c0`;
`bash -n` and six focused scale/preflight/API-wrapper unit tests passed locally.

SSH then failed first at name resolution and then by connection close to the
known controller IP. No cluster job was cancelled or submitted as a result.
Next step: re-check `44615` authoritatively; if still pending, verify the
remote script/assets, cancel only that obsolete pending job, and submit the
hash-pinned corrected-r2 validation sweep if scheduler/quota policy permits.
Do not mistake `44615`'s eventual completion for corrected-r2 validation.

## Private v1.1 suite source preflight

The two private v1.1 source banks remain gitignored; no generated cases/keys
exist and no model has seen the latest banks. Current source A SHA-256 is
`eb36aceb11eb473160083bb67139f5d34b0a3995335d699d492c52efb047fb5c`; source B
SHA-256 is `233e746e16902d6898275095320cb93243ebea7155945e5295e9006e05673570`.
Aggregate counts are 320 rows total, 40 in each of the eight target categories.

The latest independent review of A passed 160/160 rows: prompts and scenario
roots are unique, all 480 fact atoms are represented, and the reviewer found
no copy artefacts, near-duplicates, underspecification, or safety failures. A
visible shared frame remains but was assessed as non-disqualifying given the
case-specific permutations. The independent review of B found 0
underspecified rows, 0 safety failures, and 0 confirmed cross-stratum
duplicates, but flagged repeated category scaffolding, four near-duplicate
tool-honesty pairs, and three evidence-boundary prompt/fact alignment checks.
Those B issues remain unresolved; neither bank is frozen. The previous
short-prompt rejection applied to a superseded A draft and must not be reported
as the status of the current A file.
