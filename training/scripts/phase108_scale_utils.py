"""Shared MLX-to-PEFT LoRA scale conversion for Phase108 training/evaluation."""
from __future__ import annotations

import math


def mlx_scale_to_peft_alpha(scale: float, rank: int) -> float:
    """Make PEFT's ``lora_alpha / rank`` equal MLX's direct multiplier."""
    if not isinstance(scale, (int, float)) or not math.isfinite(scale) or scale <= 0:
        raise ValueError("LoRA scale must be a finite positive number")
    if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
        raise ValueError("LoRA rank must be a positive integer")
    return float(scale) * rank
