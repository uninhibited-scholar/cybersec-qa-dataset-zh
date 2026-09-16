# Architecture separation audit — 2026-10-09

Added `training/eval/architecture_audit.py` to verify path-level separation
without loading weights. It checks that the base model, candidate adapter and
Harness entrypoint are distinct and present, and rejects a candidate whose
path equals the production adapter.

The audit ran against the Mac mini and passed:

- base: `Qwen3-4B-mlx-4bit`
- candidate adapter: `phase24-depth-20260925`
- Harness: `chat_worker_router.py`
- production mutation: `false`

The first run exposed Python 3.9 compatibility in the type annotation; it was
fixed to use `Optional`, then the remote audit passed.
