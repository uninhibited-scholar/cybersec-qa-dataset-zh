#!/usr/bin/env python3
"""Metadata-only first-token sensitivity probe across fixed adapter scales."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import time

from phase108_replay_diagnostic import EXPECTED_CASE_IDS


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def eos_ids(model, tokenizer) -> set[int]:
    ids = model.generation_config.eos_token_id
    if ids is None:
        ids = tokenizer.eos_token_id
    return {ids} if isinstance(ids, int) else set(ids or [])


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--cases", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--expected-cases-sha256", required=True)
    p.add_argument("--expected-parent-sha256", required=True)
    p.add_argument("--expected-candidate-sha256", required=True)
    p.add_argument("--scales", default="0,2.5,5,10,20")
    p.add_argument("--max-new-tokens", type=int, choices=(1, 16), default=1)
    p.add_argument("--device", choices=("cpu", "cuda:0"), default="cpu")
    p.add_argument("--preflight-only", action="store_true")
    args = p.parse_args()
    hashes = {"cases": sha256(args.cases), "parent": sha256(args.parent),
              "candidate": sha256(args.candidate)}
    expected = {"cases": args.expected_cases_sha256,
                "parent": args.expected_parent_sha256,
                "candidate": args.expected_candidate_sha256}
    if hashes != expected:
        diff = ",".join(sorted(k for k in hashes if hashes[k] != expected[k]))
        raise SystemExit(f"sealed input hash mismatch: {diff}")
    scales = [float(x) for x in args.scales.split(",")]
    if scales != [0.0, 2.5, 5.0, 10.0, 20.0]:
        raise SystemExit("refusing unapproved diagnostic scales")
    selected = random.Random(20260925).sample(json.loads(args.cases.read_text()), 16)
    if [x["id"] for x in selected] != EXPECTED_CASE_IDS:
        raise SystemExit("selected IDs differ from the exposed 16-case sample")
    if args.preflight_only:
        print(json.dumps({"hashes_match": True, "selected_ids_match": True,
                          "scales": scales, "blind": False,
                          "model_load": False}, sort_keys=True), flush=True)
        return
    if args.output is None or args.output.exists():
        raise SystemExit("provide a new --output path")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from phase108_hf_adapter_smoke import attach_adapter

    tokenizer = AutoTokenizer.from_pretrained(
        str(args.base), local_files_only=True, trust_remote_code=False
    )
    adapters = (("parent", args.parent), ("candidate", args.candidate))
    records = []
    for arm, path in adapters:
        for scale in scales:
            model = AutoModelForCausalLM.from_pretrained(
                str(args.base), torch_dtype=torch.bfloat16,
                device_map=args.device, low_cpu_mem_usage=True,
                local_files_only=True, trust_remote_code=False,
            )
            model.eval()
            attach_adapter(model, path, scale=scale)
            stop_ids = eos_ids(model, tokenizer)
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
                    result = model.generate(
                        **inputs, max_new_tokens=args.max_new_tokens, do_sample=True,
                        # Keep this a short functional diagnostic, never a score.
                        temperature=0.12, top_p=0.9, repetition_penalty=1.12,
                    )
                tokens = result[0, inputs["input_ids"].shape[1]:]
                text = tokenizer.decode(tokens, skip_special_tokens=True)
                token_id = int(tokens[0]) if len(tokens) else None
                records.append({
                    "case_id": row["id"], "arm": arm, "scale": scale,
                    "adapter_sha256": hashes[arm], "first_token_id": token_id,
                    "first_token_eos": token_id in stop_ids if token_id is not None else False,
                    "decoded_empty": not bool(text.strip()),
                    "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "generated_tokens": len(tokens),
                    "max_new_tokens": args.max_new_tokens, "device": args.device,
                    "seed": seed, "seconds": round(time.monotonic() - start, 3),
                    "diagnostic_only": True, "blind": False,
                })
            del model
            if args.device.startswith("cuda"):
                torch.cuda.empty_cache()

    args.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        args.output.chmod(0o600)
        for record in records:
            f.write(json.dumps(record, sort_keys=True) + "\n")
    summary = {}
    for arm, path in adapters:
        for scale in scales:
            key = f"{arm}@{scale:g}"
            subset = [r for r in records if r["arm"] == arm and r["scale"] == scale]
            summary[key] = {"n": len(subset),
                            "first_token_eos": sum(r["first_token_eos"] for r in subset),
                            "decoded_empty": sum(r["decoded_empty"] for r in subset)}
    print(json.dumps({"summary": summary, "records": len(records),
                      "raw_prompts_or_answers_written": False,
                      "blind": False, "score": False,
                      "promotion": False}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
