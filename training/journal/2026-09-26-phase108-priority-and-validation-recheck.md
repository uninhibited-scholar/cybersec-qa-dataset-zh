# Phase108 priority and cluster recheck — 2026-09-26

## What the user challenged

The user correctly pointed out that a usable cluster service should not be
confused with candidate training/evaluation work, and asked why serving had
not been settled first. The previous response acknowledged the prioritization
mistake but did not take an action. This recheck records live state and moves
the corrected-r2 evaluation forward without changing production.

## Live service status

At 22:13 HKT, Slurm job `44601` was `RUNNING` on `a100-3` (48-hour limit).
It serves general `Qwen3-14B-BF16` with `Qwen3-1.7B` CPU fallback, and its
ready manifest explicitly says `phase108_adapter_loaded=false`. The endpoint
binds to compute-node loopback. A direct SSH/ProxyJump test to `a100-3` failed
with `Permission denied (publickey,password)`, so the laptop-side tunnel path
is not established. Do not expose the unauthenticated router on a non-loopback
interface or change production API/adapter as a workaround. This is an
internal service allocation, not yet a normally reachable API for local
clients and not the Phase108 specialist model.

## Newly verified completed jobs

- Parent baseline job `44525` completed on `dell3090` in 3m39s. It verified the
  pinned parent adapter SHA `3ed1a85e7b021e1498332a525bfa4bb75b336a03579d526f8210f1576317036`,
  frozen validation SHA
  `44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365`, 1089
  rows, rank 8, MLX scale 20, PEFT alpha/effective scale 160/20, and no train
  or test split reads. Loss: `1.7362299831`. Aggregate output SHA-256:
  `a68e6b69f224ac51c0200ecd37bab9fa28b89dd781002d4250753dbc30423a5c`.
  The one-line aggregate JSONL was copied locally and validated against those
  metadata invariants; it contains no prompt/response text.
- Public diagnostic job `44527` failed in 25s before inference. The loader
  passed unsupported keyword `dtype` to `Qwen3ForCausalLM.__init__`; there is
  no model-behavior result. Its monitor was paused after recording this
  terminal failure; no automatic retry was made.
- Job `44615` completed on `a100-1` in 3m52s, but it evaluated the
  `phase108-formatmix-20260925` and `phase108-bare-canary-20260925` adapters,
  not corrected-r2. Their fixed-validation losses were `1.7078119426` and
  `1.7372139255` respectively (1089 rows each, scale 20, no train/test read).
  These results are not evidence for corrected-r2 and must not be represented
  as such.

## Corrected-r2 validation now queued

The correct existing sweep script was copied under a distinct remote filename
and verified remotely:

- Script SHA-256:
  `f36576bf1711121ca81de6f6ce25e2f8b49de15870de1ee4e1c41662151a62c0`.
- Pinned candidate manifest SHA-256:
  `e60ae88a3f491ed94b13f9e26ef0892e5986c838f69dff2fcbf8714185a29636`.
- Corrected-r2 sweep job `44617` was submitted to `GPU-MEDIUM` for up to four
  hours. At 22:13 HKT it was `PENDING (Resources)` with no allocated node.
  It validates the numbered checkpoints and final adapter against the frozen
  1089-row `valid.jsonl` only. Its compute-side preflight verifies candidate,
  base, validator, and data hashes before inference.
- `/data3` quota was 280G / 479G (58.5%), below the 95% stop threshold.

## Local-to-compute network path probe

A short-lived, non-model HTTP probe on `a100-3`'s private address
`172.16.5.184:49081` was reachable from the Mac through an SSH local forward
terminating at the controller (`127.0.0.1:19081 -> 172.16.5.184:49081`). It
returned the expected fixed `tunnel-probe-ok` body. The probe was run as a
90-second CPU-only Slurm step inside allocation `44601`; Slurm recorded only
that test step (`44601.5`) as cancelled at its timeout, while parent service
job `44601` remained `RUNNING`. The local tunnel process was closed and the
test port was confirmed closed afterward.

This establishes that controller-to-compute private-IP forwarding works; it
does **not** make the current model API reachable, because the Qwen router is
bound to `127.0.0.1` on the compute node. Direct SSH authentication to
`a100-3` remains denied. Next transport step must be a narrowly bound,
authenticated gateway on the compute node plus this tested SSH local-forward
pattern; do not expose the current unauthenticated router directly.

At 22:24 HKT, job `44617` remained `PENDING (Resources)`, job `44601` remained
`RUNNING`, and `/data3` remained 280G / 479G (58.5%). Another user-owned job
`44619` was running on `dell3090`; it was not touched.

The fixed validation is loss/checkpoint-selection evidence only. It does not
repair empty-output behavior or establish specialist capability. Candidate
API behavior, independent blind evaluation, regression gates, rollback, and
manual confirmation remain outstanding. No production API/adapter, tools,
permissions, rubric, protocol, or candidate weights were modified.

## Next actions

1. Monitor `44617`; verify every result's hashes and row metadata, then commit
   only aggregate outputs and this journal update.
2. Separately resolve an approved local-client tunnel for the running general
   Qwen service; direct compute-node SSH is denied. Do not run a model on the
   login node, expose an unauthenticated network listener, or bypass scheduler
   controls.
3. Keep corrected-r2 isolated until fresh independent blind/regression gates
   pass. An API smoke is not deployment approval.
