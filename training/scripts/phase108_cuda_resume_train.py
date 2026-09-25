#!/usr/bin/env python3
"""Train an isolated CUDA recovery candidate from an MLX Phase108 adapter.

This runner deliberately keeps all model and evaluation boundaries explicit:
the input adapter is read-only, only prompt/completion training rows are read,
the held-out test split is never opened, and every saved checkpoint is exported
back to the MLX LoRA tensor layout for later independent evaluation on the Mini.
It does not start an API, modify production, or select a checkpoint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Iterable

import torch
from safetensors.torch import load_file, save_file
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


def read_split(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            row = json.loads(line)
            if set(row) != {"prompt", "completion"} or not all(isinstance(row[key], str) and row[key].strip() for key in row):
                raise ValueError(f"invalid prompt/completion row at {path}:{number}")
            rows.append(row)
    if not rows:
        raise ValueError(f"empty split: {path}")
    return rows


def encode_row(row: dict[str, str], tokenizer, max_length: int) -> dict[str, torch.Tensor]:
    # Transformers 5 returns a BatchEncoding from tokenized chat templates in
    # some configurations. Rendering first gives this runner one stable path.
    rendered_prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": row["prompt"]}],
        tokenize=False,
        add_generation_prompt=True,
    )
    prompt_ids = tokenizer(rendered_prompt, add_special_tokens=False)["input_ids"]
    answer_ids = tokenizer(row["completion"], add_special_tokens=False)["input_ids"] + [tokenizer.eos_token_id]
    ids = (prompt_ids + answer_ids)[:max_length]
    labels = ([-100] * len(prompt_ids) + answer_ids)[:max_length]
    if not any(label != -100 for label in labels):
        raise ValueError("completion was entirely truncated; increase max_length or filter the row")
    return {"input_ids": torch.tensor(ids), "labels": torch.tensor(labels)}


def collate(rows: Iterable[dict[str, torch.Tensor]], pad_id: int) -> dict[str, torch.Tensor]:
    rows = list(rows)
    ids = pad_sequence([row["input_ids"] for row in rows], batch_first=True, padding_value=pad_id)
    labels = pad_sequence([row["labels"] for row in rows], batch_first=True, padding_value=-100)
    return {"input_ids": ids, "attention_mask": ids.ne(pad_id), "labels": labels}


def mlx_to_peft(model, mlx_path: Path) -> None:
    """Load MLX a=[in,rank], b=[rank,out] matrices into PEFT A/B weights."""
    source = load_file(str(mlx_path), device="cpu")
    state = model.state_dict()
    installed = 0
    for key, value in source.items():
        if key.endswith(".lora_a"):
            destination = "base_model.model." + key[:-7] + ".lora_A.default.weight"
        elif key.endswith(".lora_b"):
            destination = "base_model.model." + key[:-7] + ".lora_B.default.weight"
        else:
            raise ValueError(f"unexpected MLX adapter tensor: {key}")
        if destination not in state:
            raise ValueError(f"adapter projection is absent from PEFT model: {destination}")
        target = state[destination]
        if tuple(value.T.shape) != tuple(target.shape):
            raise ValueError(f"shape mismatch {key}: mlx={tuple(value.shape)} peft={tuple(target.shape)}")
        target.copy_(value.T.to(dtype=target.dtype))
        installed += 1
    if installed != 56:
        raise ValueError(f"expected 56 MLX tensors, installed {installed}")


def mlx_adapter_layers(mlx_path: Path) -> list[int]:
    """Derive the exact layer set from the read-only MLX adapter keys."""
    state = load_file(str(mlx_path), device="cpu")
    layers: set[int] = set()
    for key in state:
        pieces = key.split(".")
        if len(pieces) < 5 or pieces[:2] != ["model", "layers"]:
            raise ValueError(f"unexpected MLX adapter tensor: {key}")
        layers.add(int(pieces[2]))
    if not layers:
        raise ValueError("adapter contains no layer projections")
    return sorted(layers)


def export_mlx(model, output: Path) -> None:
    """Export PEFT weights to the MLX tensor names/layout used by the Mini."""
    exported: dict[str, torch.Tensor] = {}
    for key, value in model.state_dict().items():
        prefix = "base_model.model.model."
        if not key.startswith(prefix):
            continue
        bare = key[len(prefix):]
        if bare.endswith(".lora_A.default.weight"):
            exported[bare.replace(".lora_A.default.weight", ".lora_a")] = value.detach().cpu().T.contiguous()
        elif bare.endswith(".lora_B.default.weight"):
            exported[bare.replace(".lora_B.default.weight", ".lora_b")] = value.detach().cpu().T.contiguous()
    if len(exported) != 56:
        raise ValueError(f"expected 56 exported MLX tensors, got {len(exported)}")
    save_file(exported, str(output))


def validation_loss(model, loader: DataLoader, device: torch.device) -> float:
    model.eval()
    losses: list[float] = []
    with torch.inference_mode():
        for batch in loader:
            batch = {name: tensor.to(device) for name, tensor in batch.items()}
            losses.append(float(model(**batch).loss))
    model.train()
    return sum(losses) / len(losses)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--adapter", required=True, type=Path)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-steps", type=int, default=7621)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accumulation", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=5e-6)
    parser.add_argument("--max-length", type=int, default=2304)
    parser.add_argument("--save-every", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260920)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is required; run this only inside a Slurm GPU allocation")
    if (args.data / "test.jsonl").exists():
        # An explicit invariant: no code path below opens it.
        print("test_split=present_not_read", flush=True)

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    device = torch.device("cuda")
    tokenizer = AutoTokenizer.from_pretrained(str(args.base), trust_remote_code=False)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    train_rows = read_split(args.data / "train.jsonl")
    valid_rows = read_split(args.data / "valid.jsonl")
    rng = random.Random(args.seed)
    validation_rows = rng.sample(valid_rows, min(32, len(valid_rows)))
    train_rows = [encode_row(row, tokenizer, args.max_length) for row in train_rows]
    validation_rows = [encode_row(row, tokenizer, args.max_length) for row in validation_rows]
    make_loader = lambda rows, shuffle: DataLoader(
        rows, batch_size=args.batch_size, shuffle=shuffle,
        collate_fn=lambda batch: collate(batch, tokenizer.pad_token_id),
    )
    valid_loader = make_loader(validation_rows, False)

    model = AutoModelForCausalLM.from_pretrained(
        str(args.base), torch_dtype=torch.bfloat16, trust_remote_code=False,
    )
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    adapter_layers = mlx_adapter_layers(args.adapter)
    mlx_lora_scale = 20.0
    lora_rank = 8
    peft_lora_alpha = mlx_scale_to_peft_alpha(mlx_lora_scale, lora_rank)
    config = LoraConfig(
        r=lora_rank, lora_alpha=peft_lora_alpha, lora_dropout=0.05,
        target_modules=list(TARGET_MODULES), layers_to_transform=adapter_layers,
        layers_pattern="layers",
        bias="none", task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, config)
    mlx_to_peft(model, args.adapter)
    model.to(device)
    model.train()
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=args.learning_rate)
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "kind": "phase108_cuda_recovery_candidate",
        "base": str(args.base), "base_config_sha256": sha256(args.base / "config.json"),
        "input_mlx_adapter": str(args.adapter), "input_mlx_adapter_sha256": sha256(args.adapter),
        "data": str(args.data), "train_rows": len(train_rows), "validation_rows_sampled": len(validation_rows),
        "test_split_read": False, "seed": args.seed, "learning_rate": args.learning_rate,
        "max_steps": args.max_steps, "max_length": args.max_length,
        "lora": {
            "rank": lora_rank,
            "mlx_scale": mlx_lora_scale,
            "peft_lora_alpha": peft_lora_alpha,
            "peft_effective_scale": peft_lora_alpha / lora_rank,
            "dropout": 0.05,
            "layers": adapter_layers,
        },
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    metrics = (args.output / "metrics.jsonl").open("w", encoding="utf-8")
    print(json.dumps({"event": "start", **manifest}, sort_keys=True), flush=True)
    train_loader = make_loader(train_rows, True)
    iterator = iter(train_loader)
    for step in range(1, args.max_steps + 1):
        optimizer.zero_grad(set_to_none=True)
        accumulated = 0.0
        for _ in range(args.grad_accumulation):
            try:
                batch = next(iterator)
            except StopIteration:
                iterator = iter(train_loader)
                batch = next(iterator)
            batch = {name: tensor.to(device) for name, tensor in batch.items()}
            loss = model(**batch).loss / args.grad_accumulation
            loss.backward()
            accumulated += float(loss) * args.grad_accumulation
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if step == 1 or step % 100 == 0:
            record = {"step": step, "train_loss": accumulated}
            if step == 1 or step % args.save_every == 0:
                record["sampled_validation_loss"] = validation_loss(model, valid_loader, device)
                output = args.output / f"{step:07d}_adapters.safetensors"
                export_mlx(model, output)
                record["mlx_adapter_sha256"] = sha256(output)
            metrics.write(json.dumps(record) + "\n")
            metrics.flush()
            print(json.dumps(record, sort_keys=True), flush=True)
    final = args.output / "adapters.safetensors"
    export_mlx(model, final)
    metrics.close()
    print(json.dumps({"event": "complete", "final_sha256": sha256(final)}), flush=True)


if __name__ == "__main__":
    main()
