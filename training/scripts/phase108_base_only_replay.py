#!/usr/bin/env python3
"""Base-only replay of the previously exposed 16-case Phase108 diagnostic."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import time

from phase108_replay_diagnostic import EXPECTED_CASE_IDS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--device", choices=("cpu", "cuda:0"), default="cuda:0")
    parser.add_argument("--max-new-tokens", type=int, default=500)
    parser.add_argument("--expected-cases-sha256", required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()

    case_sha = hashlib.sha256(args.cases.read_bytes()).hexdigest()
    if case_sha != args.expected_cases_sha256:
        raise SystemExit("private case source hash mismatch")
    rows = json.loads(args.cases.read_text())
    selected = random.Random(20260925).sample(rows, 16)
    if [row["id"] for row in selected] != EXPECTED_CASE_IDS:
        raise SystemExit("selected case IDs do not match the previously exposed sample")
    if args.preflight_only:
        print(json.dumps({"case_source_sha256": case_sha,
                          "selected_ids_match": True,
                          "preflight_only": True, "blind": False}), flush=True)
        return
    if args.output is None:
        raise SystemExit("--output is required unless --preflight-only is set")
    if args.output.exists():
        raise SystemExit("refusing to overwrite base-only diagnostic output")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.manual_seed(20260925)
    if args.device.startswith("cuda"):
        torch.cuda.manual_seed_all(20260925)
    tokenizer = AutoTokenizer.from_pretrained(
        str(args.base), local_files_only=True, trust_remote_code=False
    )
    model = AutoModelForCausalLM.from_pretrained(
        str(args.base), torch_dtype=torch.bfloat16, device_map=args.device,
        low_cpu_mem_usage=True, local_files_only=True, trust_remote_code=False,
    )
    model.eval()
    eos_ids = model.generation_config.eos_token_id or tokenizer.eos_token_id
    if isinstance(eos_ids, int):
        eos_ids = {eos_ids}
    else:
        eos_ids = set(eos_ids)
    args.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        args.output.chmod(0o600)
        for row in selected:
            rendered = tokenizer.apply_chat_template(
                row["messages"], tokenize=False, add_generation_prompt=True
            )
            inputs = tokenizer(rendered, return_tensors="pt").to(args.device)
            started = time.monotonic()
            with torch.inference_mode():
                generated = model.generate(
                    **inputs, max_new_tokens=args.max_new_tokens, do_sample=True,
                    temperature=0.12, top_p=0.9, repetition_penalty=1.12,
                )
            tokens = generated[0, inputs["input_ids"].shape[1]:]
            text = tokenizer.decode(tokens, skip_special_tokens=True)
            first_token_id = tokens[0].item() if len(tokens) else None
            first_token_eos = first_token_id in eos_ids if first_token_id is not None else False
            record = {
                "case_id": row["id"],
                "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "chars": len(text),
                "generated_tokens": len(tokens),
                "max_new_tokens": args.max_new_tokens,
                "first_token_eos": first_token_eos,
                "empty": not bool(text.strip()),
                "finish_reason": "stop" if first_token_eos else (
                    "length" if len(tokens) >= args.max_new_tokens else "stop"
                ),
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "seed": 20260925,
                "device": args.device,
                "dtype": "bfloat16",
                "adapter": None,
                "blind": False,
                "diagnostic_only": True,
            }
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
    records = [json.loads(line) for line in args.output.read_text().splitlines()]
    print(json.dumps({
        "records": len(records),
        "empty": sum(record["empty"] for record in records),
        "case_source_sha256": case_sha,
        "raw_prompts_or_answers_written": False,
        "adapter": None,
        "diagnostic_only": True,
        "blind": False,
    }), flush=True)


if __name__ == "__main__":
    main()
