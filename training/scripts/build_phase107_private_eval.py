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
CASES = EVAL_DIR / "phase107-private-cases-v0.2.json"
KEYS = EVAL_DIR / "phase107-answer-keys-v0.2.json"
ALLOWED = {
    "vulnerability_analysis", "detection_remediation", "threat_modeling",
    "code_review", "evidence_boundary", "multiturn", "tool_honesty",
    "prompt_injection",
}
SPACE = re.compile(r"\s+")
ROUND_MARKER = re.compile(r"第\s*([12])\s*轮\s*[:：]")
REQUEST_SPLIT = re.compile(r"[。！？]\s*请")


def normalize(text):
    return SPACE.sub("", unicodedata.normalize("NFKC", text)).casefold()


def to_messages(category, prompt):
    """Create the actual request sequence; keep source prompt separately for audit."""
    if category != "multiturn":
        return [{"role": "user", "content": prompt}]

    markers = list(ROUND_MARKER.finditer(prompt))
    first = next((m for m in markers if m.group(1) == "1"), None)
    second = next((m for m in markers if m.group(1) == "2"), None)
    if first is None:
        raise ValueError("multiturn fixture must contain a first-round marker")

    if second is not None:
        first_context = prompt[first.end():second.start()].strip(" \t\r\n。！？")
        followup = prompt[second.end():].strip()
    else:
        remainder = prompt[first.end():].strip()
        split = REQUEST_SPLIT.search(remainder)
        if split:
            first_context = remainder[:split.start()].strip(" \t\r\n。！？")
            followup = remainder[split.end() - 1:].strip()
        else:
            first_context = remainder.strip(" \t\r\n。！？")
            followup = "请结合前一轮材料给出结论，并区分证据、推断与未知项。"

    if not first_context or not followup:
        raise ValueError("multiturn fixture must provide initial context and a follow-up task")

    return [
        {
            "role": "user",
            "content": f"第一轮材料：{first_context}。请先作阶段性判断，区分已知事实与未知项。",
        },
        {
            "role": "assistant",
            "content": "收到。我会把当前结论限定在已提供的材料内；未核实的信息继续标注为未知，并在收到后续材料时更新判断。",
        },
        {"role": "user", "content": f"第二轮：{followup}"},
    ]


def build(require_full=False, cases_path=CASES, keys_path=KEYS, *, source_path=SOURCE,
          suite_version="phase107-v0.2", id_prefix="p107"):
    """Build one versioned private suite from an explicitly supplied fixture file.

    Defaults preserve the original Phase107 v0.2 behavior.  A later candidate
    evaluation must supply a fresh source and a distinct version/id prefix; it
    must never silently reuse an already-unsealed suite.
    """
    if not re.fullmatch(r"phase\d+-v\d+\.\d+", suite_version):
        raise ValueError("suite_version must look like phaseNN-vN.N")
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", id_prefix):
        raise ValueError("id_prefix must contain lowercase letters, digits, _ or -")
    source_bytes = source_path.read_bytes()
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
        case_id = f"{id_prefix}-{cat}-{counts[cat]:03d}"
        messages = to_messages(cat, prompt)
        message_bytes = json.dumps(messages, ensure_ascii=False, separators=(",", ":")).encode()
        prompt_hash = hashlib.sha256(n_prompt.encode()).hexdigest()
        cases.append({
            "id": case_id,
            "category": cat,
            "suite_version": suite_version,
            "prompt": prompt,
            "messages": messages,
            "conversation_sha256": hashlib.sha256(message_bytes).hexdigest(),
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
        invalid_multiturn = [
            row["id"] for row in cases
            if row["category"] == "multiturn"
            and [message["role"] for message in row["messages"]] != ["user", "assistant", "user"]
        ]
        if invalid_multiturn:
            raise ValueError(f"multiturn cases must be real user/assistant/user sequences: {invalid_multiturn}")
        multiturn_sequences = {
            normalize("\n".join(message["content"] for message in row["messages"] if message["role"] == "user"))
            for row in cases if row["category"] == "multiturn"
        }
        expected_multiturn = counts["multiturn"]
        if len(multiturn_sequences) != expected_multiturn:
            raise ValueError("multi-turn user-message sequences must be distinct")

    cases_path.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n")
    keys_path.write_text(json.dumps(keys, ensure_ascii=False, indent=2) + "\n")
    return {
        "status": "draft_not_scored",
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "suite_version": suite_version,
        "id_prefix": id_prefix,
        "case_count": len(cases),
        "category_counts": dict(sorted(counts.items())),
        "unique_normalized_prompts": len(seen_prompts),
        "structured_multiturn_cases": sum(
            row["category"] == "multiturn" and len(row["messages"]) == 3 for row in cases
        ),
        "unique_multiturn_user_sequences": len({
            normalize("\n".join(message["content"] for message in row["messages"] if message["role"] == "user"))
            for row in cases if row["category"] == "multiturn"
        }),
        "answer_key_count": len(keys),
        "prompt_manifest_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
        "answer_keys_sha256": hashlib.sha256(keys_path.read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-full", action="store_true")
    parser.add_argument("--source", type=Path, default=SOURCE,
                        help="private source fixture file; defaults to the historical v0.2 source")
    parser.add_argument("--cases-output", type=Path, default=CASES)
    parser.add_argument("--keys-output", type=Path, default=KEYS)
    parser.add_argument("--suite-version", default="phase107-v0.2")
    parser.add_argument("--id-prefix", default="p107")
    args = parser.parse_args()
    print(json.dumps(build(require_full=args.require_full, cases_path=args.cases_output,
                           keys_path=args.keys_output, source_path=args.source,
                           suite_version=args.suite_version, id_prefix=args.id_prefix),
                     ensure_ascii=False, indent=2))
