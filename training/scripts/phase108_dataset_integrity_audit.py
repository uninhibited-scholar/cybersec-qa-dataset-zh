#!/usr/bin/env python3
"""Audit exact prompt overlap without printing or persisting prompt text.

The HMAC key is generated per invocation and is never written to disk. The
optional suite-token stream allows a private benchmark's keyed fingerprints to
be compared against JSONL datasets on another trusted machine without copying
the benchmark prompts there.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
import sys
import unicodedata


SPLITS = ("train", "valid", "test")
INPUT_FIELDS = ("prompt", "question", "instruction", "input", "text", "user")


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text)).casefold()


def input_texts(row: object) -> set[str]:
    """Extract user-side text only; never include target/completion text."""
    if not isinstance(row, dict):
        return set()
    values = {
        row[field]
        for field in INPUT_FIELDS
        if isinstance(row.get(field), str) and row[field].strip()
    }
    messages = row.get("messages", [])
    if isinstance(messages, list):
        for message in messages:
            if (
                isinstance(message, dict)
                and message.get("role") == "user"
                and isinstance(message.get("content"), str)
                and message["content"].strip()
            ):
                values.add(message["content"])
    return {value for value in values if normalize(value)}


def suite_texts(path: Path) -> set[str]:
    cases = json.loads(path.read_text())
    values: set[str] = set()
    for case in cases:
        values.update(input_texts(case))
    return values


def keyed(text: str, key: bytes) -> str:
    return hmac.new(key, normalize(text).encode("utf-8"), hashlib.sha256).hexdigest()


def read_rows(path: Path) -> tuple[list[dict], int]:
    rows: list[dict] = []
    errors = 0
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return rows, 1
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            errors += 1
            continue
        if not isinstance(row, dict):
            errors += 1
            continue
        rows.append(row)
    return rows, errors


def audit(dataset_dirs: list[Path], key: bytes, suite_hashes: set[str] | None) -> dict:
    datasets: dict[str, dict[str, set[str]]] = {}
    result = {
        "status": "exact_string_scan_only",
        "dataset_dirs": [],
        "cross_dataset_exact_user_string_overlap": {},
        "limitations": [
            "Exact normalized user-text overlap only; semantic near-duplicates are not detected.",
            "A clean scan does not prove that prior checkpoints were never trained on benchmark-derived material.",
            "HMAC fingerprints and the per-run key are not persisted by this tool.",
        ],
    }
    for root in dataset_dirs:
        if not root.is_dir():
            result["dataset_dirs"].append({"path": str(root), "error": "not_a_directory"})
            continue
        split_fingerprints: dict[str, set[str]] = {split: set() for split in SPLITS}
        split_rows: dict[str, list[dict]] = {split: [] for split in SPLITS}
        split_errors: Counter[str] = Counter()
        files = []
        for split in SPLITS:
            for path in sorted(root.glob(f"{split}.jsonl")):
                rows, errors = read_rows(path)
                split_rows[split].extend(rows)
                split_errors[split] += errors
                file_prompts: set[str] = set()
                for row in rows:
                    file_prompts.update(input_texts(row))
                fingerprints = {keyed(value, key) for value in file_prompts}
                split_fingerprints[split].update(fingerprints)
                files.append({
                    "path": path.name,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "rows": len(rows),
                    "parse_errors": errors,
                    "unique_user_strings": len(fingerprints),
                    "suite_exact_overlap_strings": len(fingerprints & suite_hashes)
                    if suite_hashes is not None else None,
                })
        split_overlaps = {}
        for left, right in (("train", "valid"), ("train", "test"), ("valid", "test")):
            split_overlaps[f"{left}:{right}"] = len(split_fingerprints[left] & split_fingerprints[right])
        datasets[str(root)] = split_fingerprints
        result["dataset_dirs"].append({
            "path": str(root),
            "files": files,
            "split_rows": {split: len(split_rows[split]) for split in SPLITS},
            "split_parse_errors": dict(split_errors),
            "unique_user_strings": {split: len(split_fingerprints[split]) for split in SPLITS},
            "cross_split_exact_overlap_strings": split_overlaps,
            "suite_exact_overlap_strings": {
                split: sum(file["suite_exact_overlap_strings"] or 0 for file in files if file["path"] == f"{split}.jsonl")
                for split in SPLITS
            } if suite_hashes is not None else None,
        })
    roots = sorted(datasets)
    for index, left_root in enumerate(roots):
        for right_root in roots[index + 1:]:
            result["cross_dataset_exact_user_string_overlap"][f"{left_root}::{right_root}"] = {
                split: len(datasets[left_root][split] & datasets[right_root][split])
                for split in SPLITS
            }
    return result


def emit_suite_token(path: Path) -> None:
    key = secrets.token_bytes(32)
    hashes = {keyed(value, key) for value in suite_texts(path)}
    json.dump({"key": key.hex(), "hashes": sorted(hashes)}, sys.stdout)
    sys.stdout.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", action="append", type=Path, default=[])
    parser.add_argument("--suite", type=Path, help="private suite JSON; scan it locally")
    parser.add_argument("--emit-suite-token", action="store_true", help="emit keyed suite hashes to stdout for a trusted remote scan")
    parser.add_argument("--suite-token-stdin", action="store_true", help="read {key,hashes} from stdin")
    args = parser.parse_args()

    if args.emit_suite_token:
        if not args.suite:
            parser.error("--emit-suite-token requires --suite")
        emit_suite_token(args.suite)
        return
    if args.suite and args.suite_token_stdin:
        parser.error("use either --suite or --suite-token-stdin")
    if not args.dataset_dir:
        parser.error("at least one --dataset-dir is required")

    if args.suite_token_stdin:
        token = json.load(sys.stdin)
        key = bytes.fromhex(token["key"])
        suite_hashes = set(token["hashes"])
    else:
        key = secrets.token_bytes(32)
        suite_hashes = {keyed(value, key) for value in suite_texts(args.suite)} if args.suite else None
    json.dump(audit(args.dataset_dir, key, suite_hashes), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
