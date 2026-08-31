# Phase 6 layer ablation — 2026-08-31

Question used throughout:

> 请比较 API 返回 500、502 和 504 时最常见的故障层级，并分别给出排查优先级。

## Results

| Layer | Result |
| --- | --- |
| Qwen3-4B base, Qwen ChatML prompt | Substantive, structured answer |
| Base + Phase 6 LoRA, Qwen ChatML prompt | Substantive, structured answer |
| Base + Phase 6 LoRA, current worker prompt | Substantive answer |
| Fresh direct API conversation | Substantive answer, with one spurious `401` phrase |
| API with two prior canned evidence-gate replies in history | Empty answer |
| Harness conversation with the same bad history | Training-format residue only |

## Additional configuration defect

The locally converted base tokenizer has no configured `chat_template`.
The test therefore used Qwen's standard `<|im_start|>` / `<|im_end|>` ChatML
delimiters as a deterministic fallback. This omission should be fixed in the
model wrapper/config, rather than relying permanently on ad-hoc prompt text.

## Conclusion

The base model is not broken, and Phase 6 LoRA alone does not destroy ordinary
answering. The failure chain is:

1. An over-broad API evidence gate replaces legitimate analytical answers with
   a canned no-tool response.
2. Harness persists those incorrect assistant responses in conversation history.
3. The small model receives the complete contaminated history and subsequently
   emits an empty answer or training-format residue.

The immediate corrective priority is the API evidence gate and history handling,
not additional blind LoRA training. After repairing them, repeat the same
ablation and a fresh blind Harness suite. The spurious `401` phrase in the clean
API answer shows that model-quality work remains, but it is separate from the
catastrophic no-answer defect.

Reproduction script: `training/eval/phase6_ablation_eval.py`.
