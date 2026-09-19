"""Validate Phase 107 manifest/key structure without printing private text."""
import argparse
import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path
import re

EXPECTED = {
    "vulnerability_analysis", "detection_remediation", "threat_modeling",
    "code_review", "evidence_boundary", "multiturn", "tool_honesty",
    "prompt_injection",
}
SPACE = re.compile(r"\s+")


def normalize(text):
    return SPACE.sub("", unicodedata.normalize("NFKC", text)).casefold()


def validate(cases, keys, case_bytes=b"", key_bytes=b""):
    errors = []
    counts = Counter(row.get("category") for row in cases)
    ids = [row.get("id") for row in cases]
    key_ids = [row.get("id") for row in keys]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_case_ids")
    if len(key_ids) != len(set(key_ids)):
        errors.append("duplicate_key_ids")
    if set(ids) != set(key_ids):
        errors.append("case_key_id_mismatch")
    if set(counts) != EXPECTED or any(counts[name] != 40 for name in EXPECTED):
        errors.append("strata_must_have_40_each")
    if len(cases) < 320:
        errors.append("suite_under_320_cases")

    seen_prompts = set()
    key_by_id = {row.get("id"): row for row in keys}
    multi_sequences = set()
    for case in cases:
        cid = case.get("id", "<missing-id>")
        prompt = case.get("prompt")
        messages = case.get("messages")
        if case.get("suite_version") != "phase107-v0.2":
            errors.append(f"{cid}:wrong_suite_version")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{cid}:empty_audit_prompt")
            prompt = ""
        canonical = normalize(prompt)
        if canonical in seen_prompts:
            errors.append(f"{cid}:duplicate_normalized_prompt")
        seen_prompts.add(canonical)
        if case.get("fixture_hash") != hashlib.sha256(canonical.encode()).hexdigest():
            errors.append(f"{cid}:fixture_hash_mismatch")
        if not isinstance(messages, list) or not messages:
            errors.append(f"{cid}:missing_messages")
            continue
        if any(
            message.get("role") not in {"user", "assistant"}
            or not isinstance(message.get("content"), str)
            or not message["content"].strip()
            for message in messages
        ):
            errors.append(f"{cid}:invalid_message")
            continue
        roles = [message["role"] for message in messages]
        if case.get("category") == "multiturn":
            if roles != ["user", "assistant", "user"]:
                errors.append(f"{cid}:invalid_multiturn_roles")
            multi_sequences.add(normalize("\n".join(
                message["content"] for message in messages if message["role"] == "user"
            )))
        elif roles != ["user"] or messages[0]["content"] != prompt:
            errors.append(f"{cid}:invalid_singleturn_messages")
        serialized = json.dumps(messages, ensure_ascii=False, separators=(",", ":")).encode()
        if case.get("conversation_sha256") != hashlib.sha256(serialized).hexdigest():
            errors.append(f"{cid}:conversation_hash_mismatch")
        key = key_by_id.get(case.get("id"), {})
        for field in ("must_cover", "must_not_claim"):
            if not isinstance(key.get(field), list) or not key[field]:
                errors.append(f"{cid}:invalid_{field}")
        for field in ("evidence_boundary", "format_contract"):
            if not isinstance(key.get(field), str) or not key[field].strip():
                errors.append(f"{cid}:invalid_{field}")
        if key.get("scoring_status") != "draft_unfrozen":
            errors.append(f"{cid}:unexpected_scoring_status")

    if counts.get("multiturn", 0) != len(multi_sequences):
        errors.append("duplicate_multiturn_user_sequence")
    return {
        "status": "pass" if not errors else "fail",
        "case_count": len(cases),
        "answer_key_count": len(keys),
        "category_counts": dict(sorted(counts.items())),
        "structured_multiturn_count": sum(
            case.get("category") == "multiturn"
            and [message.get("role") for message in case.get("messages", [])] == ["user", "assistant", "user"]
            for case in cases
        ),
        "unique_multiturn_user_sequences": len(multi_sequences),
        "case_manifest_sha256": hashlib.sha256(case_bytes).hexdigest() if case_bytes else None,
        "answer_key_sha256": hashlib.sha256(key_bytes).hexdigest() if key_bytes else None,
        "error_count": len(errors),
        "errors": errors,
        "private_text_printed": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("answer_keys", type=Path)
    args = parser.parse_args()
    case_bytes, key_bytes = args.manifest.read_bytes(), args.answer_keys.read_bytes()
    result = validate(json.loads(case_bytes), json.loads(key_bytes), case_bytes, key_bytes)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
