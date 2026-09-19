#!/usr/bin/env python3
"""Create a permission-restricted blind review bundle after all arms finish.

The script never opens sealed identity-map files, never scores responses, and
refuses incomplete collections. The output directory must be outside Git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import tempfile
from pathlib import Path


RESPONSE_FIELDS = (
    "classification",
    "finish_reason",
    "transport_status",
    "first_content_s",
    "total_s",
)
KEY_FIELDS = ("must_cover", "must_not_claim", "evidence_boundary", "format_contract")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at line {line_no}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"non-object JSONL row at line {line_no}")
            rows.append(row)
    return rows


def validate_collection(cases: list[dict], responses: list[dict], run_manifest: dict) -> tuple[set[str], set[str]]:
    case_ids = {case.get("id") for case in cases}
    if len(cases) != 320 or len(case_ids) != 320 or None in case_ids:
        raise ValueError("expected 320 cases with unique IDs")
    if run_manifest.get("suite_version") != "phase107-v0.2":
        raise ValueError("unexpected suite version")
    if run_manifest.get("case_count") != len(cases):
        raise ValueError("run manifest case count mismatch")
    if run_manifest.get("answer_keys_loaded") is not False:
        raise ValueError("blind-run manifest must attest answer keys were not loaded during inference")
    required_protocol = {
        "protocol": "phase107-inference-protocol-v0.1",
        "max_tokens": 700,
        "temperature": 0.12,
        "top_p": 0.9,
        "repeat_penalty": 1.12,
        "repeat_context": 128,
        "tools": [],
        "client_retries": 0,
        "timeout_seconds": 300,
    }
    if any(run_manifest.get(key) != value for key, value in required_protocol.items()):
        raise ValueError("blind-run manifest does not match the frozen Phase 107 inference settings")

    aliases = set()
    seen: set[tuple[str, str]] = set()
    category_by_id = {case["id"]: case["category"] for case in cases}
    for row in responses:
        case_id, alias = row.get("case_id"), row.get("alias")
        if case_id not in case_ids or not isinstance(alias, str) or not alias:
            raise ValueError("response references an unknown case or empty alias")
        if row.get("category") != category_by_id[case_id]:
            raise ValueError("response category does not match the case manifest")
        key = (case_id, alias)
        if key in seen:
            raise ValueError("duplicate case/alias response")
        seen.add(key)
        aliases.add(alias)
        if not isinstance(row.get("content"), str):
            raise ValueError("response content must be a string, including for empty/error responses")

    if len(aliases) != 3:
        raise ValueError("expected exactly three blinded aliases")
    expected = {(case_id, alias) for case_id in case_ids for alias in aliases}
    if seen != expected:
        raise ValueError(f"incomplete three-arm collection: missing={len(expected - seen)} extra={len(seen - expected)}")
    return case_ids, aliases


def build_bundle(cases: list[dict], keys: list[dict], responses: list[dict], seed: int) -> list[dict]:
    case_by_id = {case["id"]: case for case in cases}
    key_by_id = {key["id"]: key for key in keys}
    if len(key_by_id) != len(keys) or set(key_by_id) != set(case_by_id):
        raise ValueError("answer-key IDs must be unique and match cases exactly")
    responses_by_id: dict[str, list[dict]] = {case_id: [] for case_id in case_by_id}
    for row in responses:
        response = {"blind_alias": row["alias"], "content": row["content"]}
        response.update({field: row.get(field) for field in RESPONSE_FIELDS})
        responses_by_id[row["case_id"]].append(response)

    ordered_cases = list(cases)
    random.Random(seed).shuffle(ordered_cases)
    bundle = []
    for index, case in enumerate(ordered_cases):
        case_id = case["id"]
        visible_responses = list(responses_by_id[case_id])
        random.Random(seed + index + 1).shuffle(visible_responses)
        key = key_by_id[case_id]
        bundle.append({
            "case_id": case_id,
            "category": case["category"],
            "messages": case["messages"],
            "answer_key": {field: key[field] for field in KEY_FIELDS},
            "responses": visible_responses,
        })
    return bundle


def write_private_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.chmod(temp_name, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_name, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--keys", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260920)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    outdir = args.outdir.expanduser().resolve()
    if outdir == repo_root or repo_root in outdir.parents:
        raise SystemExit("refusing to write reviewer material inside the Git repository")
    run_dir = args.run_dir.expanduser().resolve()
    run_manifest_path = run_dir / "blind-run-manifest.json"
    response_path = run_dir / "blind-responses.jsonl"
    if not run_manifest_path.is_file() or not response_path.is_file():
        raise SystemExit("missing completed blind run manifest or response file")

    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    cases_raw = args.cases.read_bytes()
    if hashlib.sha256(cases_raw).hexdigest() != run_manifest.get("suite_sha256"):
        raise SystemExit("run manifest does not match the supplied case-manifest hash")
    cases = json.loads(cases_raw)
    responses = read_jsonl(response_path)
    try:
        validate_collection(cases, responses, run_manifest)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    # Deliberately load answer keys only after complete three-arm coverage is proven.
    keys = json.loads(args.keys.read_text(encoding="utf-8"))
    try:
        bundle = build_bundle(cases, keys, responses, args.seed)
    except (KeyError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    write_private_jsonl(outdir / "phase107-blind-review-bundle.jsonl", bundle)
    metadata = {
        "suite_version": run_manifest["suite_version"],
        "case_count": len(bundle),
        "response_count": len(responses),
        "suite_sha256": run_manifest["suite_sha256"],
        "answer_keys_sha256": sha256(args.keys),
        "rubric": "phase107-rubric-v0.1.md",
        "rubric_sha256": sha256(repo_root / "training/eval/phase107-rubric-v0.1.md"),
        "identities_opened": False,
        "run_order_included": False,
        "identity_map_opened": False,
        "review_order_seed": args.seed,
    }
    write_private_jsonl(outdir / "phase107-blind-review-metadata.jsonl", [metadata])
    print(f"review_bundle_ready cases={len(bundle)} responses={len(responses)}; identities remain sealed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
