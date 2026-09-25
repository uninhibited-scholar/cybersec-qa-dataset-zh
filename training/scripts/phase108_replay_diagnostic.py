#!/usr/bin/env python3
"""Replay a previously exposed Phase108 sample; diagnostic only, not a score."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import time
import urllib.request


EXPECTED_CASE_IDS = [
    "p108v9-evidence_boundary-009",
    "p108v9-detection_remediation-027",
    "p108v9-tool_honesty-022",
    "p108v9-detection_remediation-021",
    "p108v9-multiturn-022",
    "p108v9-prompt_injection-010",
    "p108v9-prompt_injection-035",
    "p108v9-code_review-001",
    "p108v9-prompt_injection-011",
    "p108v9-tool_honesty-010",
    "p108v9-multiturn-002",
    "p108v9-detection_remediation-003",
    "p108v9-tool_honesty-025",
    "p108v9-code_review-016",
    "p108v9-vulnerability_analysis-005",
    "p108v9-code_review-032",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--url")
    parser.add_argument("--expected-cases-sha256", required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refusing to overwrite diagnostic output")
    case_sha = hashlib.sha256(args.cases.read_bytes()).hexdigest()
    if case_sha != args.expected_cases_sha256:
        raise SystemExit("private case source hash mismatch")
    rows = json.loads(args.cases.read_text())
    selected = random.Random(20260925).sample(rows, 16)
    ids = [row["id"] for row in selected]
    if ids != EXPECTED_CASE_IDS:
        raise SystemExit("selected case IDs do not match the previously exposed sample")

    if args.preflight_only:
        print(json.dumps({"case_source_sha256": case_sha, "selected_ids_match": True,
                          "preflight_only": True, "blind": False}), flush=True)
        return
    if args.output is None or args.url is None:
        raise SystemExit("--output and --url are required unless --preflight-only is set")

    args.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        args.output.chmod(0o600)
        for row in selected:
            payload = json.dumps(
                {"messages": row["messages"], "temperature": 0.12, "max_tokens": 500},
                ensure_ascii=False,
            ).encode()
            request = urllib.request.Request(
                args.url,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            start = time.monotonic()
            with urllib.request.urlopen(request, timeout=180) as response:
                body = json.load(response)
            text = body["choices"][0]["message"]["content"]
            row_out = {
                "case_id": row["id"],
                "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "chars": len(text),
                "empty": not bool(text.strip()),
                "finish_reason": body["choices"][0].get("finish_reason"),
                "elapsed_seconds": round(time.monotonic() - start, 3),
                "diagnostic_only": True,
                "blind": False,
            }
            stream.write(json.dumps(row_out, ensure_ascii=False) + "\n")
            stream.flush()
    print(
        json.dumps(
            {
                "records": 16,
                "empty": sum(
                    json.loads(line)["empty"]
                    for line in args.output.read_text().splitlines()
                ),
                "case_source_sha256": case_sha,
                "raw_prompts_or_answers_written": False,
                "diagnostic_only": True,
                "blind": False,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
