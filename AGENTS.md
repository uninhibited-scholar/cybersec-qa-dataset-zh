# Repository working rules

For every local-model training or evaluation change:

1. Commit reproducible configuration, data-generation/evaluation scripts, dataset counts, metrics, checkpoint selection rationale, API/Harness integration changes, and recovery commands under `training/`.
2. Update the dated journal before ending the task, including failures and negative results.
3. Never commit model weights, LoRA files, API tokens, `.env` files, private raw data, or machine credentials. Record only local paths and hashes when needed.
4. Keep generated training/validation/test sets outside Git when they contain duplicated or private material; commit the deterministic generator and split policy instead.
5. Preserve previous checkpoints and record which checkpoint is active. Do not overwrite a known-good adapter.
6. Before committing, inspect `git diff --check` and `git status`. Use a focused commit message beginning with `training:` or `eval:`.
7. Prefer the user's Mac mini for training and evaluation when the workload fits its resources. Use the school cluster when the user requests it or the Mac mini cannot reasonably run the workload.
8. When using the school cluster, synchronize reproducible code, configuration, run manifests, metrics, and recovery instructions to this Git repository at each meaningful milestone; commit and push when the remote is reachable, then verify the remote commit. Before cluster access may be lost, check for uncommitted work and record the latest job, output paths, and hashes locally.
9. Git is not a backup for model weights or private raw data. Keep those artifacts in separate approved storage with checksums and a recovery location recorded in the journal; do not claim they are backed up merely because their metadata is committed.
10. Treat 90% utilization as a hard stop for cluster storage, account quotas, GPU time, CPU time, or concurrent job limits. Check the relevant quota before submitting work; if usage reaches or approaches 90%, stop new jobs and perform cleanup/backup review first.

This file is a persistent project convention so future agents can reconstruct the training history without relying on chat context.
