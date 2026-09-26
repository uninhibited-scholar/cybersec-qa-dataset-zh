#!/usr/bin/env python3
"""Matched greedy differential on an already exposed/rejected suite.

This records only per-case metadata and aggregates. It is not a blind eval,
capability score, or candidate-promotion gate.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import time
from pathlib import Path
from urllib.request import Request, urlopen


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
    "p108v9-vulnerability_analysis-005",
    "p108v9-code_review-016",
    "p108v9-code_review-032",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def select_cases(path: Path, expected_sha256: str) -> tuple[str, list[dict]]:
    raw = path.read_bytes()
    observed = sha256_bytes(raw)
    if observed != expected_sha256:
        raise ValueError(f"case source hash mismatch: {observed}")
    rows = json.loads(raw)
    selected = random.Random(20260925).sample(rows, 16)
    if [row.get("id") for row in selected] != EXPECTED_CASE_IDS:
        raise ValueError("selected IDs differ from the already exposed v0.9 sample")
    return observed, selected


def summarize(details: list[dict]) -> dict:
    return {
        "cases": len(details),
        "empty": sum(bool(row["empty"]) for row in details),
        "nonempty": sum(not bool(row["empty"]) for row in details),
        "finish_reasons": dict(collections.Counter(str(row["finish_reason"]) for row in details)),
        "character_counts": dict(collections.Counter(str(row["chars"]) for row in details)),
        "details_metadata_sha256": sha256_bytes(
            b"".join((json.dumps(row, sort_keys=True) + "\n").encode() for row in details)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--expected-cases-sha256", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--details", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--scale", type=float, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--job-script", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--adapter-sha256", required=True)
    parser.add_argument("--server-sha256", required=True)
    parser.add_argument("--replay-sha256", required=True)
    parser.add_argument("--base-config-sha256", required=True)
    parser.add_argument("--base-index-sha256", required=True)
    args = parser.parse_args()
    if args.details.exists() or args.summary.exists():
        raise FileExistsError("refusing to overwrite diagnostic artifacts")
    adapter_sha = sha256_file(args.adapter)
    if adapter_sha != args.adapter_sha256:
        raise ValueError("adapter hash mismatch")
    if sha256_file(args.server) != args.server_sha256:
        raise ValueError("server hash mismatch")
    if sha256_file(Path(__file__)) != args.replay_sha256:
        raise ValueError("replay client hash mismatch")
    base_config_sha = sha256_file(args.base / "config.json")
    base_index_sha = sha256_file(args.base / "model.safetensors.index.json")
    if (base_config_sha, base_index_sha) != (args.base_config_sha256, args.base_index_sha256):
        raise ValueError("base model provenance mismatch")
    case_sha, selected = select_cases(args.cases, args.expected_cases_sha256)

    started = time.monotonic()
    details: list[dict] = []
    with args.details.open("x", encoding="utf-8") as output:
        args.details.chmod(0o600)
        for row in selected:
            payload = json.dumps({
                "messages": row["messages"], "temperature": 0.0,
                "max_tokens": args.max_tokens, "tools": [],
            }, ensure_ascii=False).encode()
            request = Request(args.url, data=payload, headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=180) as response:
                body = json.load(response)
            text = body["choices"][0]["message"]["content"]
            record = {
                "case_id": row["id"],
                "response_sha256": sha256_bytes(text.encode()),
                "chars": len(text),
                "empty": not bool(text.strip()),
                "finish_reason": body["choices"][0].get("finish_reason"),
                "diagnostic_only": True,
                "blind": False,
            }
            output.write(json.dumps(record, sort_keys=True) + "\n")
            output.flush()
            details.append(record)

    if len(details) != 16:
        raise RuntimeError(f"incomplete replay: {len(details)}/16")
    result = {
        "diagnostic": "matched_greedy_replay_on_exposed_v0.9",
        "blind": False,
        "capability_score": False,
        "promotion_eligible": False,
        "candidate": args.candidate,
        "adapter_sha256": adapter_sha,
        "case_source_sha256": case_sha,
        "server_sha256": sha256_file(args.server),
        "replay_client_sha256": sha256_file(Path(__file__)),
        "job_script_sha256": sha256_file(args.job_script),
        "base_config_sha256": base_config_sha,
        "base_index_sha256": base_index_sha,
        "inference": {"scale": args.scale, "temperature": 0.0, "max_tokens": args.max_tokens, "tools": []},
        **summarize(details),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "raw_prompts_or_responses_saved": False,
    }
    args.summary.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
    args.summary.chmod(0o600)
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
