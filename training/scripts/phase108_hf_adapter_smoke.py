#!/usr/bin/env python3
"""Read-only CUDA smoke test for the Phase 91 MLX LoRA adapter.

Loads the cluster's dequantized Qwen3 base, maps MLX LoRA A/B matrices onto
the matching PyTorch Linear projections without changing any files, and runs
one short generation with and without the adapter. This is a compatibility
probe only; it performs no training and saves no model outputs.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

import torch
from torch import nn
from torch.nn import functional as F
from safetensors.torch import load_file
from transformers import AutoModelForCausalLM, AutoTokenizer


class LoRAProjection(nn.Module):
    def __init__(self, base: nn.Module, a: torch.Tensor, b: torch.Tensor, scale: float):
        super().__init__()
        if a.is_meta or b.is_meta:
            raise ValueError("Adapter tensors must contain real data, not meta placeholders")
        self.base = base
        self.register_buffer("lora_a", a, persistent=False)  # [rank, in]
        self.register_buffer("lora_b", b, persistent=False)  # [out, rank]
        self.scale = scale

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Accelerate may keep base.weight on meta until its forward hook runs.
        # The new wrapper is outside that hook; its adapter must remain real.
        base_output = self.base(x)
        a = self.lora_a.to(device=x.device, dtype=x.dtype)
        b = self.lora_b.to(device=x.device, dtype=x.dtype)
        low_rank = F.linear(F.linear(x, a), b)
        return base_output + (self.scale * low_rank).to(base_output)


def attach_adapter(model: nn.Module, adapter_path: Path, scale: float) -> int:
    state = load_file(str(adapter_path), device="cpu")
    pairs: dict[str, dict[str, torch.Tensor]] = {}
    for key, tensor in state.items():
        # MLX checkpoints use either `model.layers.N...` or `layers.N...`.
        # PyTorch's Qwen module tree always uses `model.layers.N...`; accept
        # both serialized forms, then canonicalize before get_submodule().
        match = re.fullmatch(r"((?:model\.)?layers\.\d+\.(?:mlp|self_attn)\.[^.]+)\.lora_([ab])", key)
        if not match:
            raise ValueError(f"Unexpected adapter key: {key}")
        module_path = match.group(1)
        if not module_path.startswith("model."):
            module_path = "model." + module_path
        pairs.setdefault(module_path, {})[match.group(2)] = tensor

    installed = 0
    for module_path, pair in pairs.items():
        if set(pair) != {"a", "b"}:
            raise ValueError(f"Missing A/B matrix for {module_path}")
        parent_path, attr = module_path.rsplit(".", 1)
        parent = model.get_submodule(parent_path)
        base = getattr(parent, attr)
        a, b = pair["a"], pair["b"]
        if a.ndim != 2 or b.ndim != 2 or a.shape[1] != b.shape[0]:
            raise ValueError(f"Incompatible A/B shapes for {module_path}")
        if a.shape[0] != base.in_features or b.shape[1] != base.out_features:
            raise ValueError(
                f"Projection mismatch for {module_path}: base=({base.in_features},"
                f"{base.out_features}) A={tuple(a.shape)} B={tuple(b.shape)}"
            )
        device, dtype = base.weight.device, base.weight.dtype
        if device.type == "meta":
            device = torch.device("cpu")
        setattr(parent, attr, LoRAProjection(
            base,
            a.T.contiguous().to(device=device, dtype=dtype),
            b.T.contiguous().to(device=device, dtype=dtype),
            scale,
        ))
        installed += 1
    if installed != 28 or len(state) != 56:
        raise ValueError(f"Expected 28 projections / 56 tensors; got {installed}/{len(state)}")
    return installed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--adapter", required=True, type=Path)
    parser.add_argument("--scale", type=float, default=20.0)
    parser.add_argument("--max-new-tokens", type=int, default=32)
    parser.add_argument("--dtype", choices=("bfloat16", "float16"), default="bfloat16")
    parser.add_argument("--device-map", default="cuda:0")
    parser.add_argument("--gpu-memory", help="optional GPU memory cap when using device-map=auto")
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available; run inside an A100 Slurm allocation")
    capability = torch.cuda.get_device_capability(0)
    if capability < (7, 0):
        raise SystemExit(f"Unsupported CUDA SM {capability[0]}.{capability[1]}; this PyTorch build needs SM 7.0+")

    print(f"cuda_device={torch.cuda.get_device_name(0)} capability={capability}", flush=True)
    print("loading_base=true", flush=True)
    dtype = torch.bfloat16 if args.dtype == "bfloat16" else torch.float16
    load_kwargs = {}
    if args.device_map == "auto" and args.gpu_memory:
        load_kwargs["max_memory"] = {0: args.gpu_memory, "cpu": "32GiB"}
    tokenizer = AutoTokenizer.from_pretrained(str(args.base), trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        str(args.base), torch_dtype=dtype, device_map=args.device_map,
        low_cpu_mem_usage=True, trust_remote_code=False,
        **load_kwargs,
    )
    model.eval()
    prompt = "请用一句话解释最小权限原则。"
    messages = [{"role": "user", "content": prompt}]
    rendered = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    input_device = model.get_input_embeddings().weight.device
    inputs = tokenizer(rendered, return_tensors="pt").to(input_device)
    with torch.inference_mode():
        base_out = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
    base_text = tokenizer.decode(base_out[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    installed = attach_adapter(model, args.adapter, args.scale)
    with torch.inference_mode():
        adapter_out = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
    adapter_text = tokenizer.decode(adapter_out[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    if not base_text.strip() or not adapter_text.strip():
        raise SystemExit("empty_generation: compatibility gate failed")
    print(f"base_loaded=true adapter_projections={installed} adapter_tensors=56", flush=True)
    print(f"base_chars={len(base_text)} adapter_chars={len(adapter_text)}", flush=True)
    print("generation_nonempty=true", flush=True)
    print(f"peak_gpu_memory_gib={torch.cuda.max_memory_allocated()/1024**3:.3f}", flush=True)


if __name__ == "__main__":
    main()
