# Phase108 recovery — 2026-09-24

- Cluster access restored; the remote project still contains Phase108 checkpoints, logs, evaluation data, and candidate adapters.
- Resource check before submission: `/data3` was 29% used; no quota signal near the 90% stop threshold.
- Previous job 44141 failed before training because it was submitted with a wrapper executed by `/bin/sh`; `set -o pipefail` was rejected. It produced no candidate output.
- Synced the corrected training runner and direct Slurm script from the local repository to the cluster.
- Submitted isolated job 44298 directly with `sbatch` (no `--wrap`). It is currently pending in `GPU-MEDIUM` because nodes are unavailable or reserved.
- Output target: `/data3/ieug25/zj225/cyber-model-migration/models/phase108-cuda-recovery-scale20-corrected-20260924`.
- Production API, existing adapters, evaluation rubric, and tool permissions were not changed.
