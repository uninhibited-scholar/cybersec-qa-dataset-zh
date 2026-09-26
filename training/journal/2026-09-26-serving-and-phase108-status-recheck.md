# Serving and Phase108 status recheck — 2026-09-26

## Cluster serving status

At the recheck, Slurm job `44601` (`qwen14b-api-service`) was still
`PENDING (Priority)` in `GPU-LARGE`; the scheduler's current backfill estimate
was 2026-09-28 07:14 HKT. No compute node was assigned and its stdout/stderr
files were empty. Therefore there was no running Qwen3-14B API endpoint or
SSH tunnel to use. The job requests one A100-40G for the selected BF16 model
and a 48-hour bounded service allocation. The A100 nodes were occupied by
running jobs; no scheduler bypass or overlapping allocation was attempted.

The separate Phase108 fixed-validation job `44593` was also
`PENDING (Priority)` with the same estimated start. It remains an evaluation
job, not an API service. No production API, adapter, permissions, or evaluation
protocol was changed.

## Exposed-sample scale diagnostic summary

Re-aggregated existing metadata-only results for the same already-exposed
16-row v0.9 sample (`phase108-eval-private-v09` SHA-256
`9a4d398893034b922cc67582089642c553733c856ab2812088b398a2546fbb6b`). No raw
prompt or response text was read or copied into this journal.

For both the pinned parent adapter (`3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`)
and corrected-r2 adapter (`4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`),
first-token metadata shows:

- scale 0, 2.5, and 5: 0/16 first-token EOS;
- scale 10: 2/16 first-token EOS;
- scale 20: 16/16 first-token EOS.

This is an exposed functional diagnostic only, not a capability score or
blind result. It shows the immediate-stop symptom is shared by parent and
candidate at scale 20 and strongly scale-dependent in this runtime. It does
not establish which inference scale is correct or acceptable. Do not choose a
scale from these cases alone; reconcile adapter scaling semantics and use the
frozen validation plus independent blind gates before any candidate decision.

## Next actions

1. Monitor `44601`; after allocation, verify primary/fallback health and
   non-empty JSON/SSE through the loopback API and SSH tunnel before calling
   it usable. The bounded job's expiry must be reported honestly.
2. Monitor `44593`; verify candidate/manifest/validation hashes and row count.
3. Continue Phase108 root-cause work on scale semantics and output behavior;
   do not repeat training or promote a candidate until that discrepancy is
   explained and the full gates pass.
