#!/usr/bin/env python3
"""Create or verify a deterministic, read-only candidate manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def files(root: Path):
    return sorted(p for p in root.rglob("*") if p.is_file() and p.name != "candidate-manifest.json")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build(root: Path, model_version: str) -> dict:
    entries = [{"path": str(p.relative_to(root)), "sha256": sha256(p), "bytes": p.stat().st_size} for p in files(root)]
    return {"schema": "candidate-manifest-v1", "model_version": model_version,
            "candidate": str(root), "production_mutated": False, "files": entries}


def verify(root: Path, manifest: dict) -> list[str]:
    errors = []
    if manifest.get("production_mutated") is not False:
        errors.append("manifest claims production mutation")
    expected = {x["path"]: x["sha256"] for x in manifest.get("files", [])}
    actual = {str(p.relative_to(root)): sha256(p) for p in files(root)}
    if set(expected) != set(actual):
        errors.append("candidate file set changed")
    for name, digest_value in expected.items():
        if name in actual and actual[name] != digest_value:
            errors.append(f"hash mismatch: {name}")
    return errors


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--model-version", default="unknown")
    ap.add_argument("--write", action="store_true", help="write candidate-manifest.json")
    ap.add_argument("--verify", type=Path, help="verify against an existing manifest")
    args = ap.parse_args()
    if not args.root.is_dir():
        raise SystemExit("candidate directory missing")
    if args.verify:
        report = {"verified": not verify(args.root, json.loads(args.verify.read_text(encoding="utf-8"))),
                  "errors": verify(args.root, json.loads(args.verify.read_text(encoding="utf-8"))),
                  "mutated": False}
    else:
        report = build(args.root, args.model_version)
        if args.write:
            (args.root / "candidate-manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
