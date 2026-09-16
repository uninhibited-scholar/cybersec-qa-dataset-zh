#!/usr/bin/env python3
"""Collect offline agent trajectories with tamper-evident chaining.

Input is JSONL; output is JSONL marked REVIEW_REQUIRED. Nothing is promoted
to training data automatically.
"""
import argparse, hashlib, json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("output"); args = ap.parse_args()
    prev = "0" * 64; n = 0
    with Path(args.input).open(encoding="utf-8") as src, Path(args.output).open("w", encoding="utf-8") as dst:
        for line in src:
            if not line.strip(): continue
            raw = json.loads(line); n += 1
            event = {"trajectory": raw, "status": "REVIEW_REQUIRED", "training_eligible": False, "prev_hash": prev}
            event["hash"] = hashlib.sha256(json.dumps(event, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            prev = event["hash"]; dst.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"trajectories": n, "training_eligible": 0, "last_hash": prev}, ensure_ascii=False))

if __name__ == "__main__": main()
