#!/usr/bin/env python3
"""Verify the base/adapter/Harness separation without loading model weights."""
import argparse
import json
from pathlib import Path
from typing import Optional


def norm(value: str) -> Path:
    return Path(value).expanduser().resolve()


def audit(base: Path, adapter: Path, harness: Path, production: Optional[Path] = None):
    failures = []
    if base == adapter:
        failures.append("base and adapter resolve to the same path")
    if harness == base or harness == adapter:
        failures.append("Harness path overlaps a model path")
    if not base.is_dir():
        failures.append("base directory missing")
    if not adapter.is_dir():
        failures.append("adapter directory missing")
    if not harness.is_file():
        failures.append("Harness entrypoint missing")
    if production is not None and adapter == production:
        failures.append("candidate adapter is the production adapter")
    return {"passed": not failures, "failures": failures,
            "base": str(base), "adapter": str(adapter), "harness": str(harness),
            "production_mutated": False}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--harness", required=True)
    ap.add_argument("--production")
    args = ap.parse_args()
    report = audit(norm(args.base), norm(args.adapter), norm(args.harness),
                   norm(args.production) if args.production else None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 2)


if __name__ == "__main__":
    main()
