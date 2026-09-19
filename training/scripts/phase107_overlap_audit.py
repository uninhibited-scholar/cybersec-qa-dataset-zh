"""Exact normalized prompt-overlap scan for private eval suites.

Scans local train/valid/test JSONL files plus batchNNN.jsonl under the
cybersec-qa-dataset-zh dataset. Optionally includes a separate answer-key
JSON in the same exact-normalization pass. It reports paths and hashes, never row text.
An empty exact-overlap result is not proof against semantic or pretraining
contamination.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata

SPLIT_NAME = re.compile(r"(?:^|[-_])(train|training|valid|validation|test|testing)(?:[-_.]|$)", re.I)
BATCH_NAME = re.compile(r"^batch\d+\.jsonl$", re.I)


def normalize(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text)).casefold()


def prompts(row):
    values = []
    for key in ("prompt", "question", "instruction", "text", "user"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value)
    for message in row.get("messages", []):
        if message.get("role") == "user" and isinstance(message.get("content"), str):
            values.append(message["content"])
    for key in ("must_cover", "must_not_claim", "evidence_boundary", "format_contract"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value)
        elif isinstance(value, list):
            values.extend(item for item in value if isinstance(item, str) and item.strip())
    return {normalize(value) for value in values if normalize(value)}


def audit(root, suite_path, key_path=None):
    index = defaultdict(set)
    files, errors, counts = [], [], Counter()
    for path in sorted(root.rglob("*.jsonl")):
        is_dataset_batch = bool(BATCH_NAME.match(path.name))
        if not (SPLIT_NAME.search(path.stem) or is_dataset_batch):
            continue
        content = path.read_bytes()
        info = {"path": str(path.relative_to(root)), "sha256": hashlib.sha256(content).hexdigest(),
                "rows": 0, "unrecognized_rows": 0}
        for number, line in enumerate(content.decode(errors="replace").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                values = prompts(row)
                info["rows"] += 1
                if not values:
                    info["unrecognized_rows"] += 1
                for value in values:
                    index[value].add(str(path))
            except Exception as exc:
                errors.append({"path": str(path), "line": number, "type": type(exc).__name__})

        files.append(info)

    suite_bytes = suite_path.read_bytes()
    cases = json.loads(suite_bytes)
    key_bytes = key_path.read_bytes() if key_path else None
    key_rows = json.loads(key_bytes) if key_bytes else []
    keys_by_id = {row["id"]: row for row in key_rows}
    if key_path:
        case_ids = {row["id"] for row in cases}
        if len(keys_by_id) != len(key_rows) or set(keys_by_id) != case_ids:
            raise ValueError("answer-key IDs must be unique and match the suite IDs exactly")
    overlaps = []
    for case in cases:
        matches = set()
        for prompt in prompts(case):
            matches.update(index.get(prompt, ()))
        if case["id"] in keys_by_id:
            for prompt in prompts(keys_by_id[case["id"]]):
                matches.update(index.get(prompt, ()))
        if matches:
            counts[case["category"]] += 1
            overlaps.append({"id": case["id"], "sources": sorted(matches)})
    return {
        "status": "overlap_found" if overlaps else "no_exact_overlap_in_scanned_scope_not_clean_certification",
        "suite_sha256": hashlib.sha256(suite_bytes).hexdigest(),
        "answer_keys_sha256": hashlib.sha256(key_bytes).hexdigest() if key_bytes else None,
        "cases": len(cases), "answer_keys": len(key_rows), "split_files": files,
        "indexed_unique_prompts": len(index), "parse_errors": errors,
        "unrecognized_rows": sum(f["unrecognized_rows"] for f in files),
        "split_file_count": len(files), "overlapping_case_count": len(overlaps),
        "by_category": dict(counts), "overlaps": overlaps,
        "limitations": [
            "Matches any user turn, conservatively flagging shared context.",
            "Does not establish which files were consumed by each checkpoint.",
            "No semantic near-duplicate detection; no pretraining contamination claim.",
            "Scans local JSONL split files and batchNNN.jsonl files under cybersec-qa-dataset-zh; other formats, remote data, and pretraining exposure need separate lineage review.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("suite", type=Path)
    parser.add_argument("--keys", type=Path, help="optional separate answer-key JSON to include in the overlap scan")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.root, args.suite, args.keys)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered)
