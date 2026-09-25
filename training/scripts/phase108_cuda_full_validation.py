#!/usr/bin/env python3
"""Evaluate one CUDA-exported MLX adapter on the frozen Phase108 valid split.

This is deliberately a selection-only evaluator.  It refuses paths other than
``valid.jsonl``, verifies immutable hashes before and after inference, and has
no train/test, API, deployment, or checkpoint-writing code path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import torch
from safetensors.torch import load_file
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from phase108_scale_utils import mlx_scale_to_peft_alpha


TARGET_MODULES = ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_validation(path: Path, expected_hash: str) -> list[dict[str, str]]:
    if path.name != "valid.jsonl":
        raise ValueError("Only valid.jsonl may be used for checkpoint selection")
    raw = path.read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != expected_hash:
        raise ValueError(f"validation SHA-256 mismatch: {observed}")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not rows:
        raise ValueError("validation split is empty")
    for number, row in enumerate(rows, 1):
        if set(row) != {"prompt", "completion"} or not all(
            isinstance(row.get(key), str) and row[key].strip() for key in ("prompt", "completion")
        ):
            raise ValueError(f"invalid validation row {number}")
    return rows


def adapter_layers(adapter: Path) -> list[int]:
    layers: set[int] = set()
    for key in load_file(str(adapter), device="cpu"):
        parts = key.split(".")
        if len(parts) < 5 or parts[:2] != ["model", "layers"]:
            raise ValueError(f"unexpected MLX adapter key: {key}")
        layers.add(int(parts[2]))
    if layers != {32, 33, 34, 35}:
        raise ValueError(f"unexpected adapter layer topology: {sorted(layers)}")
    return sorted(layers)


def install_mlx_adapter(model, adapter: Path) -> None:
    source = load_file(str(adapter), device="cpu")
    state = model.state_dict()
    installed = 0
    for key, value in source.items():
        if key.endswith(".lora_a"):
            destination = "base_model.model." + key[:-7] + ".lora_A.default.weight"
        elif key.endswith(".lora_b"):
            destination = "base_model.model." + key[:-7] + ".lora_B.default.weight"
        else:
            raise ValueError(f"unexpected MLX adapter tensor: {key}")
        if destination not in state or tuple(value.T.shape) != tuple(state[destination].shape):
            raise ValueError(f"adapter shape/path mismatch: {key}")
        state[destination].copy_(value.T.to(dtype=state[destination].dtype))
        installed += 1
    if installed != 56:
        raise ValueError(f"expected 56 adapter tensors, got {installed}")


def encode(row: dict[str, str], tokenizer, max_length: int) -> dict[str, torch.Tensor]:
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": row["prompt"]}], tokenize=False, add_generation_prompt=True
    )
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    completion_ids = tokenizer(row["completion"], add_special_tokens=False)["input_ids"] + [tokenizer.eos_token_id]
    full_ids = prompt_ids + completion_ids
    if len(full_ids) > max_length:
        raise ValueError("validation row would be truncated; selection input is not comparable")
    return {
        "input_ids": torch.tensor(full_ids),
        "labels": torch.tensor([-100] * len(prompt_ids) + completion_ids),
    }


def collate(rows, pad_id: int) -> dict[str, torch.Tensor]:
    ids = pad_sequence([row["input_ids"] for row in rows], batch_first=True, padding_value=pad_id)
    labels = pad_sequence([row["labels"] for row in rows], batch_first=True, padding_value=-100)
    return {"input_ids": ids, "attention_mask": ids.ne(pad_id), "labels": labels}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--expected-validation-sha256", required=True)
    parser.add_argument("--expected-adapter-sha256", required=True)
    parser.add_argument("--max-length", type=int, default=2304)
    parser.add_argument("--mlx-scale", type=float, default=20.0)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("CUDA allocation required")
    adapter = args.adapter.resolve(strict=True)
    before_hash = sha256(adapter)
    if before_hash != args.expected_adapter_sha256:
        raise ValueError("adapter SHA-256 mismatch before evaluation")
    rows = read_validation(args.validation.resolve(strict=True), args.expected_validation_sha256)
    tokenizer = AutoTokenizer.from_pretrained(str(args.base), trust_remote_code=False)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    encoded = [encode(row, tokenizer, args.max_length) for row in rows]
    loader = DataLoader(encoded, batch_size=1, shuffle=False, collate_fn=lambda batch: collate(batch, tokenizer.pad_token_id))
    model = AutoModelForCausalLM.from_pretrained(str(args.base), torch_dtype=torch.bfloat16, trust_remote_code=False)
    rank = 8
    peft_alpha = mlx_scale_to_peft_alpha(args.mlx_scale, rank)
    model = get_peft_model(model, LoraConfig(
        r=rank, lora_alpha=peft_alpha, lora_dropout=0.05, target_modules=list(TARGET_MODULES),
        layers_to_transform=adapter_layers(adapter), layers_pattern="layers", bias="none", task_type="CAUSAL_LM",
    ))
    install_mlx_adapter(model, adapter)
    device = torch.device("cuda")
    model.to(device).eval()
    losses: list[float] = []
    with torch.inference_mode():
        for batch in loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            losses.append(float(model(**batch).loss))
    loss = sum(losses) / len(losses)
    if not math.isfinite(loss):
        raise ValueError("non-finite full validation loss")
    if sha256(adapter) != before_hash:
        raise ValueError("adapter changed during evaluation")
    print(json.dumps({
        "status": "complete", "validation_rows": len(rows), "validation_loss": loss,
        "validation_sha256": args.expected_validation_sha256, "adapter_sha256": before_hash,
        "base": str(args.base.resolve()), "max_length": args.max_length,
        "mlx_scale": args.mlx_scale, "lora_rank": rank,
        "peft_lora_alpha": peft_alpha, "effective_scale": peft_alpha / rank,
        "test_split_read": False, "train_split_read": False, "production_approval": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
