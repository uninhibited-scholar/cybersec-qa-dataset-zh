#!/usr/bin/env python3
"""Prepare a private, model-free semantic-independence review bundle.

It intentionally contains no model outputs or identities.  The reviewer is
asked only whether candidate fixtures represent materially distinct underlying
systems, artifacts, and decisions.  Bundle text must remain outside Git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--keys", type=Path, required=True)
    parser.add_argument("--neardup", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise SystemExit("refusing to overwrite an existing review bundle")
    source, cases, keys, triage = map(load_json, (args.source, args.cases, args.keys, args.neardup))
    case_by_id = {row["id"]: row for row in cases}
    key_by_id = {row["id"]: row for row in keys}
    source_by_fixture = {row["fixture_id"]: row for row in source}
    if len(case_by_id) != len(cases) or set(case_by_id) != set(key_by_id):
        raise SystemExit("case/key IDs must be unique and exactly aligned")
    # Cases are emitted in a deterministic but neutral order.  No model output
    # or score is present, so this cannot leak a later blind comparison.
    items = []
    for case in sorted(cases, key=lambda item: (item["category"], item["id"])):
        provenance = case.get("provenance")
        fixture_id = provenance.get("fixture_id") if isinstance(provenance, dict) else None
        if not isinstance(fixture_id, str) or not fixture_id:
            raise SystemExit(f"case lacks a source fixture reference: {case['id']}")
        fixture = source_by_fixture.get(fixture_id)
        if fixture is None:
            raise SystemExit(f"cannot locate source fixture for {case['id']}")
        items.append({
            "review_id": f"scenario-{len(items) + 1:03d}",
            "case_id": case["id"],
            "category": case["category"],
            "messages": case["messages"],
            "scenario_family": fixture["scenario_family"],
            "artifact_kind": fixture["artifact_kind"],
            "decision_focus": fixture["decision_focus"],
            "independence_rationale": fixture["independence_rationale"],
            "evidence_boundary": key_by_id[case["id"]]["evidence_boundary"],
            "review_question": "Is this a materially distinct underlying system, artifact, or decision from the other items in its stratum? Record pass, revise, or reject with a concise rationale.",
        })
    flagged = []
    for pair in triage.get("pairs", []):
        left, right = pair["ids"]
        flagged.append({"case_ids": [left, right], "similarity": pair["similarity"], "categories": pair["categories"]})
    args.output_dir.mkdir(mode=0o700)
    manifest = {
        "purpose": "semantic_independence_review_only",
        "case_count": len(items),
        "source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
        "cases_sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        "keys_sha256": hashlib.sha256(args.keys.read_bytes()).hexdigest(),
        "neardup_sha256": hashlib.sha256(args.neardup.read_bytes()).hexdigest(),
        "flagged_pair_count": len(flagged),
        "model_outputs_included": False,
        "frozen": False,
        "reviewer_must_be_independent_of_fixture_authorship": True,
    }
    for name, value in (("manifest.json", manifest), ("items.json", items), ("flagged_pairs.json", flagged)):
        path = args.output_dir / name
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        path.chmod(0o600)
    print(json.dumps({"status": "review_bundle_created", "items": len(items),
                      "flagged_pairs": len(flagged), "private_text_printed": False}))


if __name__ == "__main__":
    main()
