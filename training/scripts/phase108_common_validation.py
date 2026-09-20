#!/usr/bin/env python3
"""Evaluate one frozen checkpoint on all validation rows; no test/train reads."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import tempfile


def validation_rows(path, expected_hash):
    if path.name != "valid.jsonl":
        raise ValueError("Only valid.jsonl is allowed for checkpoint selection")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError("Validation SHA-256 mismatch")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not rows:
        raise ValueError("Empty validation dataset")
    for row in rows:
        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k].strip()
                                               for k in ("prompt", "completion")):
            raise ValueError("Expected nonempty prompt/completion validation rows")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--expected-validation-sha256", required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    rows = validation_rows(args.validation, args.expected_validation_sha256)
    checkpoint = args.checkpoint.resolve(strict=True)
    config_path = checkpoint.parent / "adapter_config.json"
    config = json.loads(config_path.read_text())
    if Path(config["model"]).resolve() != args.model.resolve():
        raise ValueError("Adapter configuration base differs from requested model")
    checkpoint_hash = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    manifest = {"validation_sha256": args.expected_validation_sha256,
                "validation_rows": len(rows), "checkpoint_sha256": checkpoint_hash,
                "checkpoint": str(checkpoint), "model": str(args.model.resolve()),
                "mask_prompt": True, "max_seq_length": 2304, "seed": 20260920,
                "test_split_loaded": False, "production_approval": False}
    if args.preflight_only:
        print(json.dumps({**manifest, "status": "preflight_only_no_inference"}))
        return
    import numpy as np
    from mlx_lm import load
    from mlx_lm.tuner.datasets import CacheDataset, CompletionsDataset
    from mlx_lm.tuner.trainer import evaluate
    with tempfile.TemporaryDirectory(prefix="phase108-validation-") as directory:
        directory = Path(directory)
        (directory / "adapters.safetensors").symlink_to(checkpoint)
        (directory / "adapter_config.json").symlink_to(config_path)
        model, tokenizer = load(str(args.model), adapter_path=str(directory))
        dataset = CacheDataset(CompletionsDataset(rows, tokenizer, "prompt", "completion", True))
        for index in range(len(dataset)):
            tokens, offset = dataset[index]
            if len(tokens) > manifest["max_seq_length"]:
                raise ValueError(f"Validation row {index} would be truncated")
            if offset < 0 or offset >= len(tokens) - 1:
                raise ValueError(f"Validation row {index} has no usable masked target")
        # Full validation coverage and identical permutation for every checkpoint.
        np.random.seed(manifest["seed"])
        loss = evaluate(model, dataset, batch_size=1, num_batches=-1, max_seq_length=2304)
    if not math.isfinite(loss):
        raise ValueError("Nonfinite validation loss")
    if hashlib.sha256(checkpoint.read_bytes()).hexdigest() != checkpoint_hash:
        raise ValueError("Checkpoint changed during evaluation")
    print(json.dumps({**manifest, "status": "complete", "validation_loss": loss}))


if __name__ == "__main__":
    main()
