"""Build a local-only Phase 107 prompt manifest and separate answer keys.

The source fixtures and generated test set are intentionally gitignored. This
script contains no prompts or secrets; only its transformation/validation
logic is committed. It is a draft builder: no model scoring is performed.
"""
import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = ROOT / "training" / "eval"
SOURCE = EVAL_DIR / "phase107-private-source-fixtures.json"
CASES = EVAL_DIR / "phase107-private-cases.json"
KEYS = EVAL_DIR / "phase107-answer-keys.json"
ALLOWED = {
    "vulnerability_analysis", "detection_remediation", "threat_modeling",
    "code_review", "evidence_boundary", "multiturn", "tool_honesty",
    "prompt_injection",
}
SPACE = re.compile(r"\s+")


def normalize(text):
    return SPACE.sub("", unicodedata.normalize("NFKC", text)).casefold()


def build(require_full=False):
    source_bytes = SOURCE.read_bytes()
    fixtures = json.loads(source_bytes)
    if not isinstance(fixtures, list) or not fixtures:
        raise ValueError("source fixture file must be a non-empty JSON list")
    counts = Counter()
    seen_prompts = set()
    seen_fixtures = set()
    cases, keys = [], []
    for row in fixtures:
        required = {"category", "prompt", "fixture_id", "must_cover", "must_not_claim", "evidence_boundary"}
        missing = required - row.keys()
        if missing:
            raise ValueError(f"fixture missing fields: {sorted(missing)}")
        cat = row["category"]
        if cat not in ALLOWED:
            raise ValueError(f"unknown category: {cat}")
        prompt = row["prompt"].strip()
        if len(prompt) < 50:
            raise ValueError(f"prompt too short: {row['fixture_id']}")
        if not all(isinstance(row[field], list) and row[field] for field in ("must_cover", "must_not_claim")):
            raise ValueError(f"answer-key lists must be non-empty: {row['fixture_id']}")
        if not row["evidence_boundary"].strip():
            raise ValueError(f"evidence boundary must be non-empty: {row['fixture_id']}")
        n_prompt = normalize(prompt)
        if n_prompt in seen_prompts:
            raise ValueError(f"duplicate normalized prompt: {row['fixture_id']}")
        if row["fixture_id"] in seen_fixtures:
            raise ValueError(f"duplicate fixture_id: {row['fixture_id']}")
        seen_prompts.add(n_prompt)
        seen_fixtures.add(row["fixture_id"])
        counts[cat] += 1
        case_id = f"p107-{cat}-{counts[cat]:03d}"
        prompt_hash = hashlib.sha256(n_prompt.encode()).hexdigest()
        cases.append({
            "id": case_id,
            "category": cat,
            "prompt": prompt,
            "fixture_hash": prompt_hash,
            "provenance": "private-authored; offline synthetic fixture",
            "rubric_ref": case_id,
        })
        keys.append({
            "id": case_id,
            "must_cover": row["must_cover"],
            "must_not_claim": row["must_not_claim"],
            "evidence_boundary": row["evidence_boundary"],
            "format_contract": row.get("format_contract", "Answer naturally; separate observation, inference, and unknowns."),
            "scoring_status": "draft_unfrozen",
        })

    if require_full:
        missing = sorted(ALLOWED - counts.keys())
        underfull = {cat: counts[cat] for cat in sorted(ALLOWED) if counts[cat] < 40}
        if missing or underfull:
            raise ValueError(f"full suite requires 40/category; missing={missing}, counts={underfull}")
        if len(cases) < 320:
            raise ValueError(f"full suite requires >=320 cases, got {len(cases)}")

    CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n")
    KEYS.write_text(json.dumps(keys, ensure_ascii=False, indent=2) + "\n")
    return {
        "status": "draft_not_scored",
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "case_count": len(cases),
        "category_counts": dict(sorted(counts.items())),
        "unique_normalized_prompts": len(seen_prompts),
        "answer_key_count": len(keys),
        "prompt_manifest_sha256": hashlib.sha256(CASES.read_bytes()).hexdigest(),
        "answer_keys_sha256": hashlib.sha256(KEYS.read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(require_full=args.require_full), ensure_ascii=False, indent=2))
