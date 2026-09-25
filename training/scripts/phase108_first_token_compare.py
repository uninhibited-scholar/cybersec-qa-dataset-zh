#!/usr/bin/env python3
"""Compare first-token termination across a base and two Phase108 adapters.

This is a diagnostic replay of an already exposed sample, not an evaluation.
It never writes prompt or answer text; only case IDs and response metadata are
persisted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import time

from phase108_replay_diagnostic import EXPECTED_CASE_IDS


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def eos_set(model, tokenizer) -> set[int]:
    value = model.generation_config.eos_token_id
    if value is None:
        value = tokenizer.eos_token_id
    if isinstance(value, int):
        return {value}
    return set(value or [])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-cases-sha256", required=True)
    parser.add_argument("--expected-parent-sha256", required=True)
    parser.add_argument("--expected-candidate-sha256", required=True)
    parser.add_argument("--device", choices=("cpu", "cuda:0"), default="cpu")
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()

    hashes = {
        "cases": hash_file(args.cases),
        "parent": hash_file(args.parent),
        "candidate": hash_file(args.candidate),
    }
    expected = {
        "cases": args.expected_cases_sha256,
        "parent": args.expected_parent_sha256,
        "candidate": args.expected_candidate_sha256,
    }
    if hashes != expected:
        mismatched = sorted(key for key in hashes if hashes[key] != expected[key])
        raise SystemExit(f"sealed input hash mismatch: {','.join(mismatched)}")
    rows = json.loads(args.cases.read_text())
    selected = random.Random(20260925).sample(rows, 16)
    if [row["id"] for row in selected] != EXPECTED_CASE_IDS:
        raise SystemExit("selected IDs differ from the exposed 16-case sample")
    if args.preflight_only:
        print(json.dumps({"hashes_match": True, "selected_ids_match": True,
                          "blind": False, "model_load": False}, sort_keys=True), flush=True)
        return
    if args.output is None or args.output.exists():
        raise SystemExit("provide a new --output path")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from phase108_hf_adapter_smoke import attach_adapter

    tokenizer = AutoTokenizer.from_pretrained(
        str(args.base), local_files_only=True, trust_remote_code=False
    )
    arms = (("base", None), ("parent", args.parent), ("candidate", args.candidate))
    args.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    records = []
    for arm, adapter in arms:
        model = AutoModelForCausalLM.from_pretrained(
            str(args.base), torch_dtype=torch.bfloat16, device_map=args.device,
            low_cpu_mem_usage=True, local_files_only=True, trust_remote_code=False,
        )
        model.eval()
        if adapter is not None:
            attach_adapter(model, adapter, scale=20.0)
        stop_ids = eos_set(model, tokenizer)
        for index, row in enumerate(selected):
            seed = 20260925 + index
            torch.manual_seed(seed)
            if args.device.startswith("cuda"):
                torch.cuda.manual_seed_all(seed)
            rendered = tokenizer.apply_chat_template(
                row["messages"], tokenize=False, add_generation_prompt=True
            )
            inputs = tokenizer(rendered, return_tensors="pt").to(args.device)
            start = time.monotonic()
            with torch.inference_mode():
                generated = model.generate(
                    **inputs, max_new_tokens=1, do_sample=True, temperature=0.12,
                    top_p=0.9, repetition_penalty=1.12,
                )
            new_tokens = generated[0, inputs["input_ids"].shape[1]:]
            text = tokenizer.decode(new_tokens, skip_special_tokens=True)
            first_id = int(new_tokens[0]) if len(new_tokens) else None
            records.append({
                "case_id": row["id"], "arm": arm,
                "adapter_sha256": (hashes[arm] if arm in hashes else None),
                "first_token_id": first_id,
                "first_token_eos": first_id in stop_ids if first_id is not None else False,
                "generated_tokens": len(new_tokens), "chars": len(text),
                "empty_after_decode": not bool(text.strip()),
                "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "elapsed_seconds": round(time.monotonic() - start, 3),
                "seed": seed, "device": args.device,
                "diagnostic_only": True, "blind": False,
            })
        del model
        if args.device.startswith("cuda"):
            torch.cuda.empty_cache()

    with args.output.open("x", encoding="utf-8") as stream:
        args.output.chmod(0o600)
        for record in records:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
    print(json.dumps({
        "records": len(records),
        "arms": {arm: sum(r["first_token_eos"] for r in records if r["arm"] == arm)
                 for arm, _ in arms},
        "empty_after_decode": {arm: sum(r["empty_after_decode"] for r in records if r["arm"] == arm)
                               for arm, _ in arms},
        "raw_prompts_or_answers_written": False,
        "blind": False, "score": False, "promotion": False,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
