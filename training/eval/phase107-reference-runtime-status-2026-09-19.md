# Phase 107 reference-runtime readiness — 2026-09-19

## Purpose and scope

This is an infrastructure-readiness note only. No Phase 107 prompts were sent to any model, no model was scored, no benchmark criterion was changed, and no production service or adapter was modified.

## Verified baseline and reference artifacts

- The Mac mini Phase 91 production API responds healthy on port 18765. Its current runtime uses `Qwen3-4B-mlx-4bit-phase3-wrapper` with `phase99-multiturn-candidate`.
- The Mac mini has a local GPT-OSS 20B GGUF reference (11,872,347,328 bytes; SHA-256 `10fe673de12c20b74b8d670a9fdf0fd36b43b0a86ffc04daeb175c0a2b98c4f9`) and Gemma 4 26B GGUF reference (16,947,541,728 bytes; SHA-256 `f2c28b3dc4776931ac6f879e11f203dec637ea0f14267a86ec8f6165f63f293f`). Each source hash was recomputed on the mini and matched after transfer to the cluster.
- Both GGUFs are now stored outside Git under `$HOME/cyber-model-migration/phase107-runtime/models/` on the school cluster. Do not load them on the mini alongside the 16 GB unified-memory production service.
- The school Slurm login environment exposes Conda (`cyber-cuda`, `dl`) but no `module`, `nvcc`, or `cmake`. Inside a scheduled A100 allocation, PyTorch 2.9.0+cu128 reported CUDA available. The system CUDA driver is 12.8-compatible.
- Installed in a separate project-local directory (not a shared environment) the official `llama.cpp` CUDA 12.8 Ubuntu x64 release `b11046`, archive SHA-256 `c27982438017c508721d8a38acedd6c746edac9c7b58517fe9a055cb61292c8a`. `llama-server` reports version `0.4.1-dev (build 11046, commit 60081bb2b)`. `libggml-cuda.so` dependencies resolve using the existing `cyber-cuda` CUDA 12 runtime/cuBLAS libraries; `llama-cli --list-devices` sees an NVIDIA A100-SXM4-40GB.
- Neutral runtime smoke jobs successfully loaded both local references on the A100 and generated `READY` for the same harmless prompt (`Say exactly READY.`). GPT-OSS completed in about 7 seconds after setup; Gemma 4 completed in about 2 minutes 17 seconds including a 16.9 GB shared-storage read. These are runnability checks only, not quality results.

## Scheduler result

At the first check, all observed A100 and RTX 3090 nodes were occupied. A 2-minute A100 probe with a 10-second immediate-start limit returned “nodes are busy” without leaving a running job. A later short probe ran on A100-3 and exited successfully.

Direct GitHub download from the cluster CPU test node was extremely throttled; that specific 10-minute job was cancelled by its owner after 34 seconds, leaving only an incomplete archive cache. The official package was then fetched on the local workstation, SHA-256 verified against the GitHub Release API, copied to the cluster, re-verified, and unpacked in a short A100 allocation. The abandoned partial download was overwritten by the verified archive. No other user's Slurm jobs were touched.

The first GPT-OSS smoke attempt used the obsolete `--conversation` flag and exited before loading weights; it was corrected to `--single-turn`. A 32-token run generated only reasoning-channel text before its token cap, so it was not counted as a completed short-answer smoke. With `--reasoning off` and 64 tokens, the final short-answer smoke passed. The Gemma 4 smoke also passed with those settings.

## Private-suite static recheck

Before any model invocation, reran the committed audits against the current files. The 320-case manifest still has 320 unique IDs, exact prompts, and targeted normalized prompt cores; all eight strata have 40 cases. The separate answer-key file has 320 matching IDs. The overlap scan must be rooted at the parent `ni-a/` directory (one level above this repository) to include both this dataset repository and the sibling Phase train/valid/test JSONL files: this reproduced the recorded 188-file / 22,315-row scope, 21,946 indexed normalized strings, zero parse errors, zero unrecognized rows, and zero exact overlaps. The result remains limited to exact normalized matches in scanned local JSONL files; it is not a semantic-cleanliness or pretraining-contamination certification.

An initial diagnostic invocation using `.` as the scan root found only the 149 dataset batch files and was discarded as an incomplete scope. The verified parent-root run is authoritative. Raw cases and answer keys were not printed or changed.

## Next safe execution sequence

1. Runtime setup and neutral single-prompt smoke checks are complete for both references. Preserve the version/hash-pinned scripts and Slurm logs.
2. The proposed inference protocol is documented at `training/eval/phase107-inference-protocol-v0.1-draft.md`; it explicitly distinguishes end-to-end endpoint comparison from raw model-weight parity because Phase 91 has worker-side guards/retries/post-processing.
3. Do not send or score the private Phase 107 suite until the draft rubric and matched inference protocol are explicitly approved/frozen. Provider-specific reasoning modes remain a separate condition.

## Reproduction

The `.sbatch` scripts are tracked under `training/eval/`. After copying them to `$HOME/cyber-model-migration/`, submit from that directory so Slurm writes logs there:

```bash
cd "$HOME/cyber-model-migration"
sbatch phase107_gpu_runtime_probe.sbatch
sbatch phase107_gptoss_runtime_smoke.sbatch
sbatch phase107_gemma4_runtime_smoke.sbatch
```

The fetch script is pinned and checksum-verifying; it refuses to overwrite an existing runtime install or a partial download. Do not rerun it after successful installation unless intentionally installing a new version into a new directory.

## Decision boundary

The reference runtime is ready. The evaluation path is waiting on explicit approval of the draft rubric and matched inference protocol. The user's general instruction to continue does not silently freeze a new scoring standard. Phase 91 production remains unchanged.

## References

- [llama.cpp CUDA build guide](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md)
- [llama.cpp GPT-OSS guide](https://github.com/ggml-org/llama.cpp/discussions/15396)
- [llama.cpp Gemma conversion support](https://github.com/ggml-org/llama.cpp/blob/master/conversion/gemma.py)
