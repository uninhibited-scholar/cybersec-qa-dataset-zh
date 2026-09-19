# 2026-09-19 — Phase 107 reference runtime readiness

## Work performed

- Reconfirmed the Mac mini Phase 91 API health and active base/adapter paths over SSH; no completion request was sent.
- Recomputed source SHA-256 values on the mini for GPT-OSS 20B GGUF (11,872,347,328 bytes; `10fe673de12c20b74b8d670a9fdf0fd36b43b0a86ffc04daeb175c0a2b98c4f9`) and Gemma 4 26B GGUF (16,947,541,728 bytes; `f2c28b3dc4776931ac6f879e11f203dec637ea0f14267a86ec8f6165f63f293f`). Transferred both to a private cluster project path and verified matching destination hashes. Model weights remain outside Git.
- Checked school Slurm partitions, queue metadata, Conda environments, and login-node tools. A100 and RTX 3090 nodes were occupied; the login shell exposed Conda but no `module`, `nvcc`, or `cmake` command.
- Requested a tightly bounded 2-minute A100 environment probe with a 10-second immediate-start bound. Slurm reported all requested nodes busy; the request exited without creating a running job. No existing jobs were changed.
- A later 2-minute A100 probe ran successfully: A100-SXM4-40GB, `cyber-cuda` PyTorch 2.9.0+cu128, CUDA available. The login-node toolchain gap remained.
- A direct GitHub download from the CPU test node was throttled; the specific job was cancelled after 34 seconds. Fetched official `llama.cpp` CUDA 12.8 release `b11046` on the local workstation, verified SHA-256 `c27982438017c508721d8a38acedd6c746edac9c7b58517fe9a055cb61292c8a`, copied it to the cluster, and unpacked it in a short A100 job. Runtime version: `0.4.1-dev`, build `11046`, commit `60081bb2b`.
- Ran neutral `READY` smoke tests on A100 for both GPT-OSS 20B and Gemma 4 26B. Both returned successfully; Gemma 4 took about 2m17s including its first 16.9 GB model read. These establish operational compatibility only, not quality.
- The first GPT-OSS command had an obsolete CLI flag and exited before loading; a second 32-token attempt was truncated within the reasoning channel; the corrected `--single-turn --reasoning off` smoke passed. No benchmark prompts were used.
- Inspected the Phase 91 worker without invoking generation. It ignores inbound Harness system messages, inserts a fixed no-tool security specialist system message, uses temp 0.12/top-p 0.9/repetition controls, and applies endpoint-side evidence/tool guards, empty/repetition retries, and post-generation transformations. Drafted a matched inference protocol that exposes this asymmetry rather than claiming raw-weight parity.
- Recorded readiness and safe next steps in `training/eval/phase107-reference-runtime-status-2026-09-19.md`.

## Evaluation and production safeguards

- No Phase 107 benchmark prompt was sent; no model score or comparison result was produced.
- The Phase 107 rubric remains a draft pending explicit approval; no scoring standards were changed.
- No training occurred. Only the pinned runtime binaries and two reference weights were transferred to private, non-Git paths; no shared Conda environment was modified.
- Existing Slurm jobs were left untouched. The two deliberately submitted smoke jobs exited normally. Phase 91 production remains unchanged.

## Next gates

1. Obtain explicit approval before freezing the proposed Phase 107 rubric and matched inference protocol.
2. Then implement and run the blinded Phase 91 + two-reference suite under that frozen protocol; keep raw prompts, answer keys, and responses outside Git.
