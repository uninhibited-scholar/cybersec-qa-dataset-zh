#!/usr/bin/env python3
"""Offline, proposal-only loop for safe model evolution experiments.

It records immutable-ish JSONL events and refuses promotion unless an
external human approval file is present. No model, tool, or production API is
ever modified by this script.
"""
import argparse, hashlib, json, time
from pathlib import Path

def digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--candidate", required=True)
    args = ap.parse_args()
    root = Path(args.root); root.mkdir(parents=True, exist_ok=True)
    events = root / "events.jsonl"
    proposal = {"candidate": args.candidate, "status": "PROPOSED",
                "production_mutation": False, "tool_permission_change": False,
                "human_approval": False, "created_at": int(time.time())}
    event = {"type": "candidate_proposal", "payload": proposal}
    event["sha256"] = digest(event)
    with events.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    approval = root / "HUMAN_APPROVAL"
    decision = "PROMOTION_BLOCKED" if not approval.exists() else "READY_FOR_HUMAN_REVIEW"
    report = {"decision": decision, "candidate": args.candidate,
              "offline_only": True, "rollback_available": True,
              "auto_promotion": False, "event_sha256": event["sha256"]}
    (root / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__":
    main()
