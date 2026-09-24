#!/usr/bin/env python3
"""Preflight a fresh, private candidate-evaluation fixture source.

This is intentionally stricter than the historical Phase107 builder.  It
checks only structural independence signals and hashes; it never prints the
private prompts or answer keys.  Passing does not establish semantic novelty,
pretraining cleanliness, or model quality.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata


EXPECTED = {
    "vulnerability_analysis", "detection_remediation", "threat_modeling",
    "code_review", "evidence_boundary", "multiturn", "tool_honesty",
    "prompt_injection",
}
REQUIRED = {
    "category", "prompt", "fixture_id", "must_cover", "must_not_claim",
    "evidence_boundary", "scenario_family", "artifact_kind", "decision_focus",
    "independence_rationale",
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text)).casefold()


def preflight(path: Path, *, expected_suite_version: str) -> dict:
    raw = path.read_bytes()
    rows = json.loads(raw)
    errors: list[str] = []
    if not isinstance(rows, list):
        return {"status": "fail", "errors": ["source_not_json_list"], "private_text_printed": False}
    counts = Counter()
    fixture_ids, prompts = set(), set()
    dimensions: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    triplets: set[tuple[str, str, str, str]] = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            errors.append(f"row_{index}:not_object")
            continue
        missing = REQUIRED - row.keys()
        if missing:
            errors.append(f"row_{index}:missing_{','.join(sorted(missing))}")
            continue
        category = row["category"]
        if category not in EXPECTED:
            errors.append(f"row_{index}:unknown_category")
            continue
        counts[category] += 1
        for key in ("fixture_id", "prompt", "scenario_family", "artifact_kind", "decision_focus", "independence_rationale"):
            if not isinstance(row[key], str) or not row[key].strip():
                errors.append(f"row_{index}:invalid_{key}")
        if not all(isinstance(row[key], list) and row[key] for key in ("must_cover", "must_not_claim")):
            errors.append(f"row_{index}:invalid_answer_key_lists")
        if isinstance(row.get("fixture_id"), str):
            if row["fixture_id"] in fixture_ids:
                errors.append(f"row_{index}:duplicate_fixture_id")
            fixture_ids.add(row["fixture_id"])
        if isinstance(row.get("prompt"), str):
            canonical = normalize(row["prompt"])
            if canonical in prompts:
                errors.append(f"row_{index}:duplicate_normalized_prompt")
            prompts.add(canonical)
        if all(isinstance(row.get(key), str) and row[key].strip() for key in ("scenario_family", "artifact_kind", "decision_focus")):
            key = (category, row["scenario_family"], row["artifact_kind"], row["decision_focus"])
            if key in triplets:
                errors.append(f"row_{index}:duplicate_scenario_artifact_decision")
            triplets.add(key)
            for dimension in ("scenario_family", "artifact_kind", "decision_focus"):
                dimensions[category][dimension].add(row[dimension])

    if set(counts) != EXPECTED or any(counts[category] != 40 for category in EXPECTED):
        errors.append("requires_exactly_40_per_category")
    for category in EXPECTED:
        if len(dimensions[category]["scenario_family"]) < 20:
            errors.append(f"{category}:too_few_scenario_families")
        if len(dimensions[category]["artifact_kind"]) < 4:
            errors.append(f"{category}:too_few_artifact_kinds")
        if len(dimensions[category]["decision_focus"]) < 8:
            errors.append(f"{category}:too_few_decision_foci")
    return {
        "status": "pass" if not errors else "fail",
        "suite_version": expected_suite_version,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "case_count": len(rows),
        "category_counts": dict(sorted(counts.items())),
        "unique_fixture_ids": len(fixture_ids),
        "unique_normalized_prompts": len(prompts),
        "diversity": {category: {name: len(values) for name, values in sorted(dimensions[category].items())}
                      for category in sorted(EXPECTED)},
        "error_count": len(errors),
        "errors": errors,
        "private_text_printed": False,
        "limitations": [
            "Structural diversity is not a semantic-duplicate proof.",
            "A clean scan cannot prove absence of pretraining contamination.",
            "A passed source remains draft until independent review freezes its hashes.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--suite-version", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = preflight(args.source, expected_suite_version=args.suite_version)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        if args.output.exists():
            raise SystemExit("refusing to overwrite existing preflight result")
        args.output.write_text(rendered)
        args.output.chmod(0o600)
    print(rendered)
    raise SystemExit(0 if result["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
