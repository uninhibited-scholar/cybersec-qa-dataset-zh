#!/usr/bin/env python3
"""Compare PEFT training-path and manual MLX-adapter forward math.

Diagnostic only: one fixed generic prompt, no generation, no validation/test or
blind data, and no prompt/response text in the output. The JSON summary only
contains logit-difference and EOS/top-token metadata.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

from phase108_hf_adapter_smoke import LoRAProjection, attach_adapter
from phase108_cuda_full_validation import adapter_layers, install_mlx_adapter


TARGET_MODULES = ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")
GENERIC_PROMPT = "Say hello in one word."
EXPOSED_CASE_SHA = "9a4d398893034b922cc67582089642c553733c856ab2812088b398a2546fbb6b"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_base(base: Path) -> tuple[torch.nn.Module, AutoTokenizer]:
    tokenizer = AutoTokenizer.from_pretrained(
        str(base), local_files_only=True, trust_remote_code=False
    )
    model = AutoModelForCausalLM.from_pretrained(
        str(base), torch_dtype=torch.float16, device_map="cuda:0",
        low_cpu_mem_usage=True, local_files_only=True, trust_remote_code=False,
    )
    model.eval()
    return model, tokenizer


def make_inputs(model, tokenizer) -> tuple[torch.Tensor, torch.Tensor]:
    rendered = tokenizer.apply_chat_template(
        [{"role": "user", "content": GENERIC_PROMPT}],
        tokenize=False,
        add_generation_prompt=True,
    )
    encoded = tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
    device = model.get_input_embeddings().weight.device
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)
    return input_ids, attention_mask


def last_logits(model, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    with torch.inference_mode():
        return model(input_ids=input_ids, attention_mask=attention_mask).logits[0, -1].float().cpu()


def summarize_logits(logits: torch.Tensor, eos_id: int) -> dict[str, int | float]:
    top = torch.topk(logits, k=2)
    eos_logit = float(logits[eos_id])
    eos_rank = int((logits > logits[eos_id]).sum()) + 1
    return {
        "top1_token_id": int(top.indices[0]),
        "top1_logit": float(top.values[0]),
        "top1_top2_margin": float(top.values[0] - top.values[1]),
        "eos_token_id": eos_id,
        "eos_logit": eos_logit,
        "eos_rank": eos_rank,
        "eos_minus_top1": eos_logit - float(top.values[0]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--expected-adapter-sha256", required=True)
    parser.add_argument("--expected-base-config-sha256", required=True)
    parser.add_argument("--case-source", type=Path,
                        help="optional already-exposed v0.9 cases file for a failing-case probe")
    parser.add_argument("--case-id", help="case ID from the already-exposed diagnostic sample")
    parser.add_argument("--expected-case-source-sha256")
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("CUDA allocation required; do not run on the login node")
    adapter_sha = sha256(args.adapter)
    if adapter_sha != args.expected_adapter_sha256:
        raise ValueError("adapter SHA-256 mismatch")
    base_config_sha = sha256(args.base / "config.json")
    if base_config_sha != args.expected_base_config_sha256:
        raise ValueError("base config SHA-256 mismatch")

    if bool(args.case_source) != bool(args.case_id):
        raise ValueError("--case-source and --case-id must be provided together")
    if args.case_source:
        expected_case_sha = args.expected_case_source_sha256 or EXPOSED_CASE_SHA
        if expected_case_sha != EXPOSED_CASE_SHA or sha256(args.case_source) != EXPOSED_CASE_SHA:
            raise ValueError("only the already-exposed v0.9 diagnostic source is allowed")
        rows = json.loads(args.case_source.read_text(encoding="utf-8"))
        selected = next((row for row in rows if row.get("id") == args.case_id), None)
        if selected is None or not isinstance(selected.get("messages"), list):
            raise ValueError("requested exposed case is missing or malformed")
        messages = selected["messages"]
        case_source_sha = EXPOSED_CASE_SHA
    else:
        messages = [{"role": "user", "content": GENERIC_PROMPT}]
        case_source_sha = None

    tokenizer_for_eos = AutoTokenizer.from_pretrained(
        str(args.base), local_files_only=True, trust_remote_code=False
    )
    eos_id = int(tokenizer_for_eos.eos_token_id)
    del tokenizer_for_eos

    # First, measure the base and custom manual MLX-layout wrapper in one load.
    manual_model, tokenizer = load_base(args.base)
    if case_source_sha:
        rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        encoded = tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
        input_device = manual_model.get_input_embeddings().weight.device
        input_ids = encoded["input_ids"].to(input_device)
        attention_mask = encoded["attention_mask"].to(input_device)
    else:
        input_ids, attention_mask = make_inputs(manual_model, tokenizer)
    base_logits = last_logits(manual_model, input_ids, attention_mask)
    installed = attach_adapter(manual_model, args.adapter, scale=20.0)
    manual20_logits = last_logits(manual_model, input_ids, attention_mask)
    for module in manual_model.modules():
        if isinstance(module, LoRAProjection):
            module.scale = 1.0
    manual1_logits = last_logits(manual_model, input_ids, attention_mask)
    del manual_model, tokenizer, input_ids, attention_mask
    gc.collect()
    torch.cuda.empty_cache()

    # Then independently measure PEFT's training-path implementation at the
    # declared effective scale, using the same immutable base and adapter.
    peft_model, tokenizer = load_base(args.base)
    layers = adapter_layers(args.adapter)
    peft_model = get_peft_model(peft_model, LoraConfig(
        r=8, lora_alpha=160, lora_dropout=0.05,
        target_modules=list(TARGET_MODULES), layers_to_transform=layers,
        layers_pattern="layers", bias="none", task_type="CAUSAL_LM",
    ))
    install_mlx_adapter(peft_model, args.adapter)
    peft_model.eval()
    if case_source_sha:
        rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        encoded = tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
        input_device = peft_model.get_input_embeddings().weight.device
        input_ids = encoded["input_ids"].to(input_device)
        attention_mask = encoded["attention_mask"].to(input_device)
    else:
        input_ids, attention_mask = make_inputs(peft_model, tokenizer)
    peft20_logits = last_logits(peft_model, input_ids, attention_mask)

    difference = manual20_logits - peft20_logits
    cosine = torch.nn.functional.cosine_similarity(
        manual20_logits.unsqueeze(0), peft20_logits.unsqueeze(0), dim=1
    )[0]
    print(json.dumps({
        "status": "complete",
        "diagnostic_only": True,
        "blind": False,
        "generation_performed": False,
        "raw_prompt_or_response_saved": False,
        "case_id": args.case_id,
        "case_source_sha256": case_source_sha,
        "adapter_sha256": adapter_sha,
        "base_config_sha256": base_config_sha,
        "lora_rank": 8,
        "mlx_scale": 20.0,
        "peft_alpha": 160.0,
        "peft_effective_scale": 20.0,
        "projection_count": installed,
        "input_token_count": int(attention_mask.sum()),
        "manual_vs_peft": {
            "max_abs_logit_diff": float(difference.abs().max()),
            "mean_abs_logit_diff": float(difference.abs().mean()),
            "cosine_similarity": float(cosine),
            "argmax_equal": int(manual20_logits.argmax()) == int(peft20_logits.argmax()),
        },
        "base": summarize_logits(base_logits, eos_id),
        "manual_scale20": summarize_logits(manual20_logits, eos_id),
        "manual_scale1": summarize_logits(manual1_logits, eos_id),
        "peft_scale20": summarize_logits(peft20_logits, eos_id),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("torch", "transformers", "peft", "safetensors")
        },
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
