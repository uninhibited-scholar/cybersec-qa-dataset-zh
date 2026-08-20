# Repository working rules

For every local-model training or evaluation change:

1. Commit reproducible configuration, data-generation/evaluation scripts, dataset counts, metrics, checkpoint selection rationale, API/Harness integration changes, and recovery commands under `training/`.
2. Update the dated journal before ending the task, including failures and negative results.
3. Never commit model weights, LoRA files, API tokens, `.env` files, private raw data, or machine credentials. Record only local paths and hashes when needed.
4. Keep generated training/validation/test sets outside Git when they contain duplicated or private material; commit the deterministic generator and split policy instead.
5. Preserve previous checkpoints and record which checkpoint is active. Do not overwrite a known-good adapter.
6. Before committing, inspect `git diff --check` and `git status`. Use a focused commit message beginning with `training:` or `eval:`.

This file is a persistent project convention so future agents can reconstruct the training history without relying on chat context.
