# Phase108 fixed-validation reproducibility rerun — 2026-09-27

## Authoritative job result

- CUHK Slurm job `44617` (`p108-r2-valscale20`) completed on `dell3090` with
  exit code `0:0`; elapsed time was 25m19s (2026-09-26 23:53:51 to
  2026-09-27 00:19:10 HKT).
- The rerun evaluated all nine pinned adapter checkpoints against the same
  frozen validation file, SHA-256
  `44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365`,
  1089 rows each.
- Each row records rank 8, MLX scale 20, PEFT alpha 160/effective scale 20,
  no train/test split reads, and no production approval. Candidate/checkpoint
  hashes matched the submitted sweep manifest. The log ended with
  `PHASE108_FIXED_SCALE_VALIDATION=PASS`.
- Local aggregate JSONL SHA-256:
  `7a0d59d5b9119270693a680bfd5d7ff5e4f74864f12fff546be854404ef08ade`.
  This file is byte-for-byte identical to the full nine-row result from job
  `44518`; only aggregate validation metrics/metadata are retained locally.

## Interpretation

The candidate validation loss decreases monotonically from 1.736240571 at the
first checkpoint to 1.706258487 at the final checkpoint. The parent adapter's
fixed-scale validation loss from job `44525` was 1.736229983. This is a
reproducible validation-loss signal, not evidence of improved cyber capability
or production readiness; exposed functional diagnostics previously found a
serious empty-output failure, and the independent blind evaluation has not yet
run.

## Serving-path distinction

At the last read-only check, service job `44601` was healthy for `qwen3-14b-bf16`
with its CPU fallback, but `ready.json` explicitly reported
`phase108_adapter_loaded: false`. Thus the cluster's current API service is not
the Phase108 cyber-adapter model. It was not changed here.

No adapter, production API, benchmark rubric/protocol, permission, or candidate
weight was changed. The fixed-validation result does not authorize deployment.
