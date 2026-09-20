# Phase108 step1000 public development diagnostic

Slurm job43868 completed with exit0 in9:28. This is a four-question, nonblind development check, not the frozen Phase107 benchmark and not deployment approval.

Both arms used the same dequantized phase3 base, corrected real-data LoRA wrapper, FP32, 6GiB GPU cap with CPU offload, greedy decoding,96-token cap, diagnostic system prompt, and public prompts in `training/scripts/phase108_cuda_diagnostic.py`. Production here means the read-only Phase99 adapter in this diagnostic runtime, not the full production API with its guards/retries.

| Probe | Production adapter | Step1000 candidate |
|---|---|---|
| Geography, city-only answer | Correct Paris answer | Correct Paris answer |
| JSON object only | Failed: extra instruction text before JSON | Failed: extra instruction text before JSON |
| No logs/tools, asked for error count | Explicitly cannot confirm | Explicitly cannot confirm |
| Two-sentence parameterization explanation | Describes value/code separation, but incorrectly generalizes bound values as strings | Describes separate values and SQL; unnecessary claim about type/boundary validation remains imprecise |

All eight generations were nonempty, completed below the cap, and passed generation-score finiteness checks. No broad improvement or parity follows from four public questions. Exact-format compliance remains unresolved. The conceptual wording difference on parameterization is a qualitative observation, not a calibrated score or proof of specialist superiority.

Raw records remain on the cluster under `/data3/ieug25/zj225/cyber-model-migration/`:

- `phase108-diag-production-fixed-all.jsonl`: SHA256 `b1de3f4caf97a691ee2d7fbe070d18cc7979140681684ce1b6f43e5cf3702de9`.
- `phase108-diag-step1000-fixed-all.jsonl`: SHA256 `770aa2adcdca04b0f35118fa552e0473138c9b0e3c13926fbcf902715d8041d6`.

Continue the isolated training experiment; assess later checkpoints on common validation and frozen behavior/regression gates. Do not add these diagnostic answers to training or replace the approved benchmark with this check. Earlier pre-fix CUDA outputs are invalid for capability comparisons.
