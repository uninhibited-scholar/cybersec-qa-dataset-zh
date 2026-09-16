#!/usr/bin/env python3
"""Promote explicitly reviewed trajectories into an isolated staging set."""
import argparse, json
from pathlib import Path

ap=argparse.ArgumentParser(); ap.add_argument("scores"); ap.add_argument("trajectories"); ap.add_argument("staging"); ap.add_argument("--approval", required=True); ap.add_argument("--min-score", type=float, default=.9); a=ap.parse_args()
approval=Path(a.approval)
if not approval.exists(): raise SystemExit("approval file required")
try: approved={int(x.strip()) for x in approval.read_text().splitlines() if x.strip()}
except ValueError: raise SystemExit("approval file must contain numeric trajectory ids")
scores=json.loads(Path(a.scores).read_text(encoding="utf-8"))["results"]
selected={r["index"] for r in scores if r["index"] in approved and r["score"] >= a.min_score and not r["reasons"]}
rows=Path(a.trajectories).read_text(encoding="utf-8").splitlines()
out=Path(a.staging); out.mkdir(parents=True, exist_ok=True)
with (out/"approved.jsonl").open("w",encoding="utf-8") as f:
    for i,line in enumerate(rows,1):
        if i in selected: f.write(line+"\n")
report={"approved_ids":sorted(selected),"count":len(selected),"min_score":a.min_score,"staging_only":True,"production_mutation":False,"auto_promotion":False}
(out/"review-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False))
