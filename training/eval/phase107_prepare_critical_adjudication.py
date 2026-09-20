#!/usr/bin/env python3
"""Validate blinded Phase 107 review ledgers and emit private adjudication packets.

The script never opens the alias-to-system map. Input ledgers and output packets
must stay outside Git because packets contain private prompts, keys and answers.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL: {path}:{line_no}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"expected JSON object: {path}:{line_no}")
            rows.append(value)
    return rows


def ledger_rows(paths: list[Path], reviewer: str) -> dict[tuple[int, str, str], dict]:
    result: dict[tuple[int, str, str], dict] = {}
    for path in paths:
        for row in read_jsonl(path):
            # These are superseded partial exports. Keep valid portions only.
            if reviewer == "B" and path.name == "reviewer-b-101-120.jsonl" and 116 <= row.get("row", -1) <= 120:
                continue
            if reviewer == "C" and path.name == "reviewer-c-critical.jsonl" and row.get("row", -1) < 244:
                continue
            key = (row.get("row"), row.get("case_id"), row.get("alias"))
            if not all(key) or not isinstance(key[0], int):
                raise ValueError(f"invalid row/case/alias identity in {path}")
            if key in result:
                raise ValueError(f"duplicate reviewer {reviewer} ledger key: {key}")
            result[key] = row
    return result


def expected_rows(bundle: list[dict]) -> dict[tuple[int, str, str], dict]:
    expected: dict[tuple[int, str, str], dict] = {}
    for index, case in enumerate(bundle, 1):
        case_id = case.get("case_id")
        for response in case.get("responses", []):
            key = (index, case_id, response.get("blind_alias"))
            if key in expected:
                raise ValueError(f"duplicate bundle key: {key}")
            expected[key] = {"case": case, "response": response}
    if len(bundle) != 320 or len(expected) != 960:
        raise ValueError("expected exactly 320 cases and 960 blinded responses")
    return expected


def validate_ledger(name: str, rows: dict, expected: dict) -> int:
    missing = set(expected) - set(rows)
    extra = set(rows) - set(expected)
    if missing or extra:
        raise ValueError(f"reviewer {name}: missing={len(missing)} extra={len(extra)}")
    state_diffs = 0
    for key, item in rows.items():
        actual = item.get("response_state")
        authoritative = expected[key]["response"].get("classification")
        if actual != authoritative:
            # Raw bundle classification is authoritative for operational state.
            state_diffs += 1
        if not isinstance(item.get("critical"), bool):
            raise ValueError(f"reviewer {name}: critical must be boolean at {key}")
        scores = item.get("scores")
        if name in {"A", "B"} and scores is not None:
            if not isinstance(scores, list) or len(scores) != 4 or any(
                not isinstance(score, int) or score not in (0, 1, 2) for score in scores
            ):
                raise ValueError(f"reviewer {name}: invalid score vector at {key}")
    return state_diffs


def secure_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(content)
    os.chmod(path, 0o600)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--a-ledger", required=True, nargs="+", type=Path)
    parser.add_argument("--b-ledger", required=True, nargs="+", type=Path)
    parser.add_argument("--c-ledger", required=True, nargs="+", type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--cases-per-packet", type=int, default=20)
    args = parser.parse_args()
    if args.cases_per_packet < 1:
        parser.error("--cases-per-packet must be positive")

    bundle = read_jsonl(args.bundle)
    expected = expected_rows(bundle)
    ledgers = {
        "A": ledger_rows(args.a_ledger, "A"),
        "B": ledger_rows(args.b_ledger, "B"),
        "C": ledger_rows(args.c_ledger, "C"),
    }
    state_diffs = {name: validate_ledger(name, rows, expected) for name, rows in ledgers.items()}

    adjudication_cases: list[dict] = []
    vote_counts = {"unanimous_no": 0, "unanimous_yes": 0, "disputed": 0}
    candidate_responses = 0
    excluded_by_case_rule = 0
    for row_index, case in enumerate(bundle, 1):
        case_id = case["case_id"]
        responses = []
        flags: list[bool] = []
        for response in case["responses"]:
            alias = response["blind_alias"]
            key = (row_index, case_id, alias)
            judgments = {name: ledger[key] for name, ledger in ledgers.items()}
            votes = {name: judgment["critical"] for name, judgment in judgments.items()}
            flags.append(any(votes.values()))
            if len(set(votes.values())) == 1:
                vote_counts["unanimous_yes" if next(iter(votes.values())) else "unanimous_no"] += 1
            else:
                vote_counts["disputed"] += 1
            if any(votes.values()):
                candidate_responses += 1
            responses.append({
                "alias": alias,
                "response_state": response.get("classification"),
                "finish_reason": response.get("finish_reason"),
                "content": response.get("content"),
                "reviewer_flags": {
                    name: {
                        "critical": judgment["critical"],
                        "type": judgment.get("critical_type"),
                        "evidence_quote": judgment.get("evidence_quote"),
                    }
                    for name, judgment in judgments.items()
                },
            })
        if case_id == "p107-prompt_injection-024":
            # Frozen bundle calibration excludes it from model-failure counting.
            excluded_by_case_rule += sum(flags)
            continue
        if any(flags):
            adjudication_cases.append({
                "row": row_index,
                "case_id": case_id,
                "category": case.get("category"),
                "messages": case.get("messages"),
                "answer_key": case.get("answer_key"),
                "responses": responses,
            })

    size = args.cases_per_packet
    packet_paths: list[str] = []
    for start in range(0, len(adjudication_cases), size):
        group = adjudication_cases[start : start + size]
        number = start // size + 1
        packet = args.out_dir / f"phase107-critical-adjudication-{number:02d}.jsonl"
        text = "".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n" for record in group)
        secure_write(packet, text)
        packet_paths.append(str(packet))

    summary = {
        "status": "blind_adjudication_packets_prepared",
        "cases": len(bundle),
        "response_records": len(expected),
        "critical_candidate_cases": len(adjudication_cases),
        "critical_candidate_responses_before_case_exclusions": candidate_responses,
        "candidate_flags_excluded_by_frozen_case_rule": excluded_by_case_rule,
        "reviewer_vote_pattern_counts": vote_counts,
        "reviewer_state_metadata_differences_from_bundle": state_diffs,
        "identity_map_opened": False,
        "packets": packet_paths,
    }
    secure_write(args.out_dir / "phase107-critical-adjudication-summary.json", json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
