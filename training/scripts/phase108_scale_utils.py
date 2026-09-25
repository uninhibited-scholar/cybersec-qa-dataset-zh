"""Shared MLX-to-PEFT LoRA scale conversion for Phase108 training/evaluation."""
from __future__ import annotations

import math
import re


def mlx_scale_to_peft_alpha(scale: float, rank: int) -> float:
    """Make PEFT's ``lora_alpha / rank`` equal MLX's direct multiplier."""
    if not isinstance(scale, (int, float)) or not math.isfinite(scale) or scale <= 0:
        raise ValueError("LoRA scale must be a finite positive number")
    if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
        raise ValueError("LoRA rank must be a positive integer")
    return float(scale) * rank


def canonical_mlx_lora_key(key: str) -> tuple[str, int, str]:
    """Normalize MLX `layers.N...` and `model.layers.N...` tensor keys.

    Returns (canonical_module_path, transformer_layer, factor), where factor
    is `a` or `b`. This is metadata-only and does not load a model.
    """
    match = re.fullmatch(
        r"(?:(model)\.)?layers\.(\d+)\.(?:mlp|self_attn)\.[^.]+\.lora_([ab])",
        key,
    )
    if not match:
        raise ValueError(f"unexpected MLX adapter key: {key}")
    has_model, layer_text, factor = match.groups()
    canonical = key if has_model else "model." + key
    return canonical.rsplit(".lora_", 1)[0], int(layer_text), factor


def mlx_key_to_peft_state_key(key: str) -> str:
    """Map an MLX A/B tensor key to its corresponding PEFT state-dict key."""
    module_path, _layer, factor = canonical_mlx_lora_key(key)
    peft_factor = "A" if factor == "a" else "B"
    return f"base_model.model.{module_path}.lora_{peft_factor}.default.weight"
