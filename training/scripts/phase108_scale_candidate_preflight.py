#!/usr/bin/env python3
"""Verify scale provenance of an isolated Phase108 candidate before evaluation.

This checker reads only the candidate manifest and weights.  It is deliberately
not an evaluator, selector, deployment tool, or model loader.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(candidate: Path, expected_input_sha256: str) -> dict:
    manifest_path = candidate / "manifest.json"
    final_adapter = candidate / "adapters.safetensors"
    if not manifest_path.is_file() or not final_adapter.is_file():
        raise ValueError("candidate must contain manifest.json and adapters.safetensors")
    manifest = json.loads(manifest_path.read_bytes())
    if manifest.get("kind") != "phase108_cuda_recovery_candidate":
        raise ValueError("unexpected candidate manifest kind")
    if manifest.get("input_mlx_adapter_sha256") != expected_input_sha256:
        raise ValueError("input adapter hash does not match the sealed source")
    if manifest.get("test_split_read") is not False:
        raise ValueError("candidate manifest does not prove test split isolation")
    lora = manifest.get("lora")
    if not isinstance(lora, dict):
        raise ValueError("candidate manifest has no LoRA provenance")
    rank = lora.get("rank")
    mlx_scale = lora.get("mlx_scale")
    peft_alpha = lora.get("peft_lora_alpha")
    effective = lora.get("peft_effective_scale")
    if not isinstance(rank, int) or rank < 1 or not all(isinstance(value, (int, float))
                                                         for value in (mlx_scale, peft_alpha, effective)):
        raise ValueError("malformed LoRA scale provenance")
    if not math.isclose(float(peft_alpha) / rank, float(mlx_scale), rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("PEFT alpha/rank does not equal the MLX direct scale")
    if not math.isclose(float(effective), float(mlx_scale), rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("manifest effective scale does not equal the MLX direct scale")
    return {
        "status": "scale_preflight_passed_no_inference",
        "candidate": str(candidate.resolve()),
        "candidate_adapter_sha256": sha256(final_adapter),
        "input_adapter_sha256": expected_input_sha256,
        "rank": rank,
        "mlx_scale": mlx_scale,
        "peft_lora_alpha": peft_alpha,
        "test_split_read": False,
        "deployment_approval": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--expected-input-sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.candidate, args.expected_input_sha256), sort_keys=True))


if __name__ == "__main__":
    main()
