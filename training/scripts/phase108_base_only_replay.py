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
    torch.cuda.manual_seed_all(20260925)
    tokenizer = AutoTokenizer.from_pretrained(
        str(args.base), local_files_only=True, trust_remote_code=False
    )
    model = AutoModelForCausalLM.from_pretrained(
        str(args.base), torch_dtype=torch.bfloat16, device_map="cuda:0",
        low_cpu_mem_usage=True, local_files_only=True, trust_remote_code=False,
    )
    model.eval()
    args.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        args.output.chmod(0o600)
        for row in selected:
            rendered = tokenizer.apply_chat_template(
                row["messages"], tokenize=False, add_generation_prompt=True
            )
            inputs = tokenizer(rendered, return_tensors="pt").to("cuda:0")
            started = time.monotonic()
            with torch.inference_mode():
                generated = model.generate(
                    **inputs, max_new_tokens=500, do_sample=True,
                    temperature=0.12, top_p=0.9, repetition_penalty=1.12,
                )
            tokens = generated[0, inputs["input_ids"].shape[1]:]
            text = tokenizer.decode(tokens, skip_special_tokens=True)
            record = {
                "case_id": row["id"],
                "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "chars": len(text),
                "generated_tokens": len(tokens),
                "empty": not bool(text.strip()),
                "finish_reason": "length" if len(tokens) >= 500 else "stop",
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "seed": 20260925,
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
