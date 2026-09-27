#!/usr/bin/env python3
"""Prepare a private, identity-blind reviewer bundle for Phase108 v1.8-rev2.

This is an adapter to the already-frozen Phase107 rubric, not a rubric change.
It requires completed, hash-verified inference; never reads the identity map;
and writes prompts, answer keys, and responses only to a new private directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import stat
import sys

# This script is launched from training/eval, while the shared provenance
# verifier lives in training/scripts. Resolve that sibling directory so the
# CLI works from any current working directory.
_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from phase108_verify_blind_collection_v18r2 import (
    ALIASES,
    EXPECTED_CASES_SHA,
    EXPECTED_FREEZE_SHA,
    EXPECTED_KEY_SHA,
    EXPECTED_SYSTEM_PROMPT_SHA,
    sha256_file,
    verify_collection,
    verify_slurm,
)


EXPECTED_RUBRIC_SHA = "e1015d0930a98f5978b1b5e1f1fb8b9e820d2943de74489ff3ceda8249e8c9bd"
EXPECTED_PROTOCOL_SHA = "344c0c34b8c18552f015f01f82b554545b36ee4eb12ffe510c766eb2cbafd12c"
EXPECTED_PROTOCOL_CORRIGENDUM_SHA = "2e73351e65e1a053450c265986f1aa79aaec2fe4a9f20dcadebcd67693f1758b"
EXPECTED_CASES = 320
EXPECTED_RESPONSES = EXPECTED_CASES * len(ALIASES)
EXPECTED_STRATA = {
    "code_review",
    "detection_remediation",
    "evidence_boundary",
    "multiturn",
    "prompt_injection",
    "threat_modeling",
    "tool_honesty",
    "vulnerability_analysis",
}
KEY_FIELDS = ("must_cover", "must_not_claim", "evidence_boundary", "format_contract")


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid or unreadable JSON: {path.name}") from exc


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    try:
        with path.open(encoding="utf-8") as stream:
            for line_no, line in enumerate(stream, 1):
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"malformed JSONL: {path.name}:{line_no}") from exc
                if not isinstance(value, dict):
                    raise ValueError(f"expected JSON object: {path.name}:{line_no}")
                rows.append(value)
    except OSError as exc:
        raise ValueError(f"unreadable JSONL: {path.name}") from exc
    return rows


def private_dir(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(path, 0o700)


def private_write(path: Path, text: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(path, 0o600)


def response_state(row: dict) -> str:
    if row.get("empty") is True:
        return "empty"
    if row.get("finish_reason") == "length":
        return "truncated"
    return "ok"


def validate_case_and_key_rows(cases: list[dict], keys: list[dict]) -> tuple[dict, dict]:
    if len(cases) != EXPECTED_CASES or len(keys) != EXPECTED_CASES:
        raise ValueError("expected exactly 320 cases and 320 answer keys")
    case_by_id = {row.get("id"): row for row in cases}
    key_by_id = {row.get("id"): row for row in keys}
    if None in case_by_id or len(case_by_id) != EXPECTED_CASES:
        raise ValueError("case IDs are missing or duplicated")
    if None in key_by_id or len(key_by_id) != EXPECTED_CASES:
        raise ValueError("answer-key IDs are missing or duplicated")
    if set(case_by_id) != set(key_by_id):
        raise ValueError("answer-key IDs do not match frozen cases")
    counts: dict[str, int] = {}
    for case_id, case in case_by_id.items():
        category = case.get("category")
        messages = case.get("messages")
        if category not in EXPECTED_STRATA or not isinstance(messages, list) or not messages:
            raise ValueError(f"case structure invalid for {case_id}")
        if any(not isinstance(m, dict) or m.get("role") not in {"user", "assistant"}
               or not isinstance(m.get("content"), str) for m in messages):
            raise ValueError(f"case messages invalid for {case_id}")
        counts[category] = counts.get(category, 0) + 1
        key = key_by_id[case_id]
        if any(field not in key for field in KEY_FIELDS):
            raise ValueError(f"answer-key schema incomplete for {case_id}")
    if set(counts) != EXPECTED_STRATA or any(count != 40 for count in counts.values()):
        raise ValueError("frozen stratum counts must be 40 per category")
    return case_by_id, key_by_id


def build_review_bundle(cases: list[dict], keys: list[dict], responses: list[dict], seed: int) -> list[dict]:
    case_by_id, key_by_id = validate_case_and_key_rows(cases, keys)
    if len(responses) != EXPECTED_RESPONSES:
        raise ValueError("expected exactly 960 responses")
    grouped: dict[str, dict[str, dict]] = {case_id: {} for case_id in case_by_id}
    for row in responses:
        case_id, alias = row.get("case_id"), row.get("alias")
        if case_id not in case_by_id or alias not in ALIASES:
            raise ValueError("response references unknown case or alias")
        if alias in grouped[case_id]:
            raise ValueError("duplicate response for case/alias")
        response = row.get("response")
        if not isinstance(response, str):
            raise ValueError("response must be a string, including empty responses")
        if row.get("response_sha256") != hashlib.sha256(response.encode()).hexdigest():
            raise ValueError("response digest mismatch")
        grouped[case_id][alias] = row
    if any(set(by_alias) != ALIASES for by_alias in grouped.values()):
        raise ValueError("incomplete blinded case/alias matrix")

    ordered_ids = list(case_by_id)
    random.Random(seed).shuffle(ordered_ids)
    bundle = []
    for position, case_id in enumerate(ordered_ids):
        case, key = case_by_id[case_id], key_by_id[case_id]
        response_items = []
        for alias, row in grouped[case_id].items():
            response_items.append({
                "blind_alias": alias,
                "content": row["response"],
                "response_state": response_state(row),
                "finish_reason": row.get("finish_reason"),
                "generated_tokens": row.get("generated_tokens"),
                "latency_seconds": row.get("latency_seconds"),
                "tool_marker": row.get("tool_marker"),
                "unclosed_thinking": row.get("unclosed_thinking"),
            })
        random.Random(seed + position + 1).shuffle(response_items)
        bundle.append({
            "case_id": case_id,
            "category": case["category"],
            "messages": case["messages"],
            "answer_key": {field: key[field] for field in KEY_FIELDS},
            "responses": response_items,
        })
    return bundle


def prepare(run_dir: Path, cases_path: Path, freeze_path: Path, keys_path: Path,
            rubric_path: Path, protocol_path: Path, corrigendum_path: Path,
            outdir: Path, repo_root: Path, job_id: str, integrity_job_id: str,
            seed: int, slurm_runner=None) -> dict:
    outdir = outdir.expanduser().resolve()
    repo_root = repo_root.expanduser().resolve()
    if outdir == repo_root or repo_root in outdir.parents:
        raise ValueError("refusing to write private reviewer materials inside the Git repository")
    if outdir.exists():
        raise ValueError("review output path already exists")

    report_path = run_dir / "integrity-report.json"
    report_stat = report_path.stat()
    if stat.S_IMODE(report_stat.st_mode) & 0o077:
        raise ValueError("integrity report is not private")
    report = read_json(report_path)
    if (report.get("status") != "verified_blind_collection_integrity"
            or report.get("identity_map_read") is not False
            or report.get("labels_revealed") is not False):
        raise ValueError("required verified-but-blind integrity report is missing")

    current_collection = verify_collection(
        run_dir, cases_path, freeze_path, job_id,
        slurm_runner if slurm_runner is not None else __import__("subprocess").run,
    )
    verify_slurm(integrity_job_id, slurm_runner if slurm_runner is not None else __import__("subprocess").run)
    if report.get("summaries_by_blind_alias") != current_collection.get("summaries_by_blind_alias"):
        raise ValueError("saved integrity report differs from re-verified response summaries")

    expected_inputs = (
        (cases_path, EXPECTED_CASES_SHA, "cases"),
        (freeze_path, EXPECTED_FREEZE_SHA, "freeze"),
        (keys_path, EXPECTED_KEY_SHA, "answer keys"),
        (rubric_path, EXPECTED_RUBRIC_SHA, "rubric"),
        (protocol_path, EXPECTED_PROTOCOL_SHA, "protocol"),
        (corrigendum_path, EXPECTED_PROTOCOL_CORRIGENDUM_SHA, "protocol corrigendum"),
    )
    for path, expected, label in expected_inputs:
        if sha256_file(path) != expected:
            raise ValueError(f"pinned {label} hash mismatch")

    cases, keys = read_json(cases_path), read_json(keys_path)
    response_rows = []
    for alias in sorted(ALIASES):
        response_rows.extend(read_jsonl(run_dir / f"responses-{alias}.jsonl"))
    bundle = build_review_bundle(cases, keys, response_rows, seed)

    metadata = {
        "review_bundle": "phase108_v1.8-rev2_blind_review",
        "suite_freeze_sha256": EXPECTED_FREEZE_SHA,
        "cases_sha256": EXPECTED_CASES_SHA,
        "answer_keys_sha256": EXPECTED_KEY_SHA,
        "rubric_sha256": EXPECTED_RUBRIC_SHA,
        "protocol_sha256": EXPECTED_PROTOCOL_SHA,
        "protocol_corrigendum_sha256": EXPECTED_PROTOCOL_CORRIGENDUM_SHA,
        "system_prompt_sha256": EXPECTED_SYSTEM_PROMPT_SHA,
        "parent_adapter_sha256": current_collection["parent_sha256"],
        "candidate_adapter_sha256": current_collection["candidate_sha256"],
        "responses_by_blind_alias": current_collection["summaries_by_blind_alias"],
        "run_job_id": job_id,
        "integrity_job_id": integrity_job_id,
        "case_count": EXPECTED_CASES,
        "response_count": EXPECTED_RESPONSES,
        "strata_per_case_count": 40,
        "identity_map_opened": False,
        "labels_revealed": False,
        "scored": False,
        "deployment_eligible": False,
        "review_order_seed": seed,
        "case_order_shuffled": True,
        "response_order_shuffled_per_case": True,
    }
    private_dir(outdir)
    bundle_path = outdir / "phase108-v18r2-blind-review-bundle.jsonl"
    bundle_text = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in bundle)
    private_write(bundle_path, bundle_text)
    metadata["bundle_sha256"] = sha256_file(bundle_path)
    metadata_text = json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    private_write(outdir / "metadata.json", metadata_text)
    return {
        "status": "blind_review_bundle_ready",
        "case_count": EXPECTED_CASES,
        "response_count": EXPECTED_RESPONSES,
        "bundle_sha256": metadata["bundle_sha256"],
        "identity_map_opened": False,
        "labels_revealed": False,
        "output_dir": str(outdir),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--keys", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--corrigendum", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--integrity-job-id", required=True)
    parser.add_argument("--seed", type=int, default=20260927)
    args = parser.parse_args()
    try:
        result = prepare(
            args.run_dir, args.cases, args.freeze, args.keys, args.rubric,
            args.protocol, args.corrigendum, args.outdir, args.repo_root,
            args.job_id, args.integrity_job_id, args.seed,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "rejected", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
