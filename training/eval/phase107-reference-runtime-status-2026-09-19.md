# Phase 107 reference-runtime readiness — 2026-09-19

## Purpose and scope

This is an infrastructure-readiness note only. No Phase 107 prompts were sent to any model, no model was scored, no benchmark criterion was changed, and no production service or adapter was modified.

## Verified baseline and reference artifacts

- The Mac mini Phase 91 production API responds healthy on port 18765. Its current runtime uses `Qwen3-4B-mlx-4bit-phase3-wrapper` with `phase99-multiturn-candidate`.
- The mini has a local GPT-OSS 20B GGUF reference artifact (~11 GB) and Gemma 4 26B GGUF reference artifact (~16 GB). These are too large to load alongside the 16 GB unified-memory production service; do not run them on the mini.
- The school Slurm environment lists A100-40G nodes and RTX 3090 resources. Its login node has no `module`, `nvcc`, or `cmake` command in the observed shell; Conda exists, with `cyber-cuda` and `dl` environments. Toolchain/CUDA availability must be inspected inside a scheduled GPU allocation, not inferred from the login node.

## Scheduler result

At the time of this check, all observed A100 and RTX 3090 nodes were occupied by other scheduled jobs. A 2-minute, 1×A100-40G, 2-CPU, 4-GB memory runtime probe was requested with a 10-second immediate-start limit; Slurm reported that requested nodes were busy and returned without leaving a running probe job. Existing jobs were not inspected beyond queue metadata, attached to, interrupted, or modified.

## Next safe execution sequence

1. When a GPU slot is available, run a short infrastructure-only allocation probe: GPU identity, CUDA visibility, Python/PyTorch CUDA availability, available CMake/compiler, and whether a compatible `llama.cpp` binary is already present.
2. If required software is absent, install/build only in a user-owned Conda/prefix or scratch directory under a scheduled allocation; never compile on the login node. Preserve the environment recipe and logs.
3. Smoke-test a reference model with a neutral non-benchmark prompt and no tools. Do not load the large references on the Mac mini.
4. Do not run or score the private Phase 107 suite until the draft rubric and matched inference protocol have been explicitly approved/frozen. Any eventual comparison must use the same production system prompt, user prompts, tool inventory (empty), context policy, decoding budget, parser, and timeout/retry rules; provider-specific reasoning modes remain a separate condition.

## Decision boundary

The infrastructure path is currently waiting on GPU scheduler availability. Independently, the evaluation path is waiting on explicit approval of the draft rubric. The user's general instruction to continue does not silently freeze a new scoring standard. Phase 91 production remains unchanged.

## References

- [llama.cpp CUDA build guide](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md)
- [llama.cpp GPT-OSS guide](https://github.com/ggml-org/llama.cpp/discussions/15396)
- [llama.cpp Gemma conversion support](https://github.com/ggml-org/llama.cpp/blob/master/conversion/gemma.py)
