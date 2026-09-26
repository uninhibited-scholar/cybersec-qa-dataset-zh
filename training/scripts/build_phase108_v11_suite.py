#!/usr/bin/env python3
"""Build a private Phase108 v1.1 case/key pair from two reviewed source banks.

This is a packaging/validation utility, not a content generator or approval
gate. It never prints private prompts or answer keys, and refuses to overwrite
any output. Source banks and outputs are expected to be gitignored.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unicodedata


VERSION = "phase108-v1.1"
CATEGORIES = (
    "vulnerability_analysis", "detection_remediation", "threat_modeling",
    "code_review", "evidence_boundary", "multiturn", "tool_honesty",
    "prompt_injection",
)
REQUIRED = {
    "category", "fixture_id", "scenario_root_id", "scenario_family",
    "artifact_kind", "decision_focus", "independence_rationale",
    "scenario_facts", "prompt", "must_cover", "must_not_claim",
    "evidence_boundary", "format_contract",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text)).casefold()


def _validate_messages(row: dict, index: int) -> list[dict]:
    messages = row.get("messages")
    if row["category"] != "multiturn":
        if messages is not None:
            raise ValueError(f"row {index}: messages are reserved for multiturn cases")
        return [{"role": "user", "content": row["prompt"]}]
    if not isinstance(messages, list) or len(messages) < 3 or len(messages) > 7:
        raise ValueError(f"row {index}: multiturn messages must contain 3-7 turns")
    roles = [m.get("role") for m in messages if isinstance(m, dict)]
    if len(roles) != len(messages) or roles[:3] != ["user", "assistant", "user"]:
        raise ValueError(f"row {index}: multiturn must start user-assistant-user")
    if roles[-1] != "user" or any(r not in {"user", "assistant"} for r in roles):
        raise ValueError(f"row {index}: multiturn must end with a user turn")
    if any(not isinstance(m.get("content"), str) or not m["content"].strip() for m in messages):
        raise ValueError(f"row {index}: empty or invalid message content")
    if any(roles[i] == roles[i - 1] for i in range(1, len(roles))):
        raise ValueError(f"row {index}: multiturn roles must alternate")
    return messages


def build(source_paths: list[Path]) -> tuple[list[dict], list[dict], dict]:
    if len(source_paths) != 2:
        raise ValueError("exactly two independent source banks are required")
    all_rows: list[dict] = []
    source_hashes = []
    for path in source_paths:
        raw = path.read_bytes()
        source_hashes.append({"name": path.name, "sha256": sha256(raw)})
        rows = json.loads(raw)
        if not isinstance(rows, list):
            raise ValueError(f"source bank is not a JSON list: {path.name}")
        all_rows.extend(rows)

    counts = Counter()
    roots: set[str] = set()
    facts: set[str] = set()
    prompts: set[str] = set()
    fixture_ids: set[str] = set()
    triplets: set[tuple[str, str, str, str]] = set()
    grouped: dict[str, list[dict]] = {name: [] for name in CATEGORIES}
    for index, row in enumerate(all_rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"row {index}: expected an object")
        missing = REQUIRED - row.keys()
        if missing:
            raise ValueError(f"row {index}: missing required fields")
        category = row["category"]
        if category not in grouped:
            raise ValueError(f"row {index}: unknown category")
        counts[category] += 1
        for field in ("fixture_id", "scenario_root_id", "scenario_family", "artifact_kind",
                      "decision_focus", "independence_rationale", "prompt",
                      "evidence_boundary", "format_contract"):
            if not isinstance(row[field], str) or not row[field].strip():
                raise ValueError(f"row {index}: invalid required text field")
        if len(row["prompt"]) < 60:
            raise ValueError(f"row {index}: prompt too short to convey a concrete case")
        for field in ("must_cover", "must_not_claim"):
            values = row[field]
            if not isinstance(values, list) or not values or any(not isinstance(x, str) or not x.strip() for x in values):
                raise ValueError(f"row {index}: invalid {field}")
        row_facts = row["scenario_facts"]
        if not isinstance(row_facts, list) or len(row_facts) < 2 or any(not isinstance(x, str) or not x.strip() for x in row_facts):
            raise ValueError(f"row {index}: invalid scenario facts")
        normalized_facts = [normalize(x) for x in row_facts]
        if len(set(normalized_facts)) != len(normalized_facts) or facts.intersection(normalized_facts):
            raise ValueError(f"row {index}: duplicate scenario-fact atom")
        facts.update(normalized_facts)
        norm_prompt = normalize(row["prompt"])
        if norm_prompt in prompts:
            raise ValueError(f"row {index}: duplicate normalized prompt")
        prompts.add(norm_prompt)
        root = normalize(row["scenario_root_id"])
        if root in roots:
            raise ValueError(f"row {index}: duplicate scenario root across suite")
        roots.add(root)
        fixture = normalize(row["fixture_id"])
        if fixture in fixture_ids:
            raise ValueError(f"row {index}: duplicate fixture id")
        fixture_ids.add(fixture)
        triplet = (category, row["scenario_family"], row["artifact_kind"], row["decision_focus"])
        if triplet in triplets:
            raise ValueError(f"row {index}: repeated category/family/artifact/decision combination")
        triplets.add(triplet)
        grouped[category].append(row)
        _validate_messages(row, index)

    if set(counts) != set(CATEGORIES) or any(counts[name] != 40 for name in CATEGORIES):
        raise ValueError("expected exactly 40 source cases per required category")

    cases: list[dict] = []
    keys: list[dict] = []
    for category in CATEGORIES:
        for ordinal, row in enumerate(grouped[category], 1):
            case_id = f"p108v11-{category}-{ordinal:03d}"
            source_fingerprint = sha256(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                                   separators=(",", ":")).encode())
            cases.append({
                "id": case_id,
                "suite_version": VERSION,
                "category": category,
                "messages": _validate_messages(row, len(cases) + 1),
                "prompt": row["prompt"],
                "rubric_ref": "phase107-rubric-v0.1",
                "fixture_hash": source_fingerprint,
                "provenance": {
                    "fixture_id": row["fixture_id"],
                    "scenario_root_id": row["scenario_root_id"],
                    "scenario_family": row["scenario_family"],
                    "artifact_kind": row["artifact_kind"],
                    "decision_focus": row["decision_focus"],
                    "independence_rationale": row["independence_rationale"],
                    "scenario_facts": row["scenario_facts"],
                },
            })
            keys.append({
                "id": case_id,
                "must_cover": row["must_cover"],
                "must_not_claim": row["must_not_claim"],
                "evidence_boundary": row["evidence_boundary"],
                "format_contract": row["format_contract"],
                "fixture_hash": source_fingerprint,
                "scoring_status": "unscored",
            })
    metadata = {
        "suite_version": VERSION,
        "case_count": len(cases),
        "category_counts": dict(sorted(counts.items())),
        "unique_scenario_roots": len(roots),
        "unique_fact_atoms": len(facts),
        "source_banks": source_hashes,
        "rubric_ref": "phase107-rubric-v0.1",
        "blind": False,
        "frozen": False,
        "deployment_approval": False,
        "private_text_printed": False,
    }
    return cases, keys, metadata


def write_new(path: Path, value: object) -> str:
    rendered = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(rendered)
    path.chmod(0o600)
    return sha256(rendered)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_a", type=Path)
    parser.add_argument("source_b", type=Path)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--keys", type=Path, required=True)
    args = parser.parse_args()
    cases, keys, metadata = build([args.source_a, args.source_b])
    case_sha = write_new(args.cases, cases)
    try:
        key_sha = write_new(args.keys, keys)
    except Exception:
        # Do not leave a misleading one-sided case/key package behind.
        args.cases.unlink(missing_ok=True)
        raise
    metadata.update({"cases_sha256": case_sha, "keys_sha256": key_sha})
    print(json.dumps(metadata, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
