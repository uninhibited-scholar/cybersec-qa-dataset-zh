#!/usr/bin/env python3
"""Build an isolated Phase108 prompt-format mix without changing source data."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

PATTERN = re.compile(r"^.*?问题：(?P<question>.*)\n回答：$", re.S)

def transform(row: dict, index: int, ratio: float) -> dict:
    prompt = row.get("prompt")
    if not isinstance(prompt, str):
        raise ValueError(f"row {index}: prompt is not text")
    match = PATTERN.match(prompt)
    if not match:
        raise ValueError(f"row {index}: unexpected prompt wrapper")
    # Deterministic selection keeps the artifact reproducible and preserves
    # the original row order.  The source row itself is never modified.
    digest = int(hashlib.sha256(f"{index}:{prompt}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    out = dict(row)
    if digest < ratio:
        out["prompt"] = match.group("question")
    return out

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--bare-ratio", type=float, default=0.5)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit("refusing to overwrite output")
    args.output.mkdir(parents=True)
    for split in ("train", "valid"):
        src = args.source / f"{split}.jsonl"
        dst = args.output / f"{split}.jsonl"
        with src.open() as inp, dst.open("x") as out:
            for i, line in enumerate(inp, 1):
                row = json.loads(line)
                out.write(json.dumps(transform(row, i, args.bare_ratio), ensure_ascii=False) + "\n")
    manifest = {"source": str(args.source), "bare_ratio": args.bare_ratio,
                "transform": "strip fixed 问题/回答 wrapper deterministically",
                "splits": ["train", "valid"]}
    (args.output / "formatmix-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

if __name__ == "__main__":
    main()
