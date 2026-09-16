#!/usr/bin/env python3
import json, subprocess, tempfile
from pathlib import Path

def main():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        p = subprocess.run(["python3", "phase12-evolution-sandbox.py", "--root", str(root), "--candidate", "candidate"], capture_output=True, text=True, check=True)
        report = json.loads(p.stdout)
        assert report["decision"] == "PROMOTION_BLOCKED"
        assert report["offline_only"] and report["rollback_available"]
        assert report["auto_promotion"] is False
        lines = (root / "events.jsonl").read_text().splitlines()
        assert len(lines) == 1 and json.loads(lines[0])["type"] == "candidate_proposal"
    print("phase12 evolution sandbox test: 4/4 assertions passed")

if __name__ == "__main__":
    main()
