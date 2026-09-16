#!/usr/bin/env python3
"""Reject malformed trajectories before scoring or training."""
import argparse, json
from pathlib import Path

def check(x):
    if not isinstance(x, dict): return "record_not_object"
    if "trajectory" in x: return "unexpected_nested_trajectory"
    if not isinstance(x.get("response"), str): return "missing_response"
    if "tool_receipts" in x and not isinstance(x["tool_receipts"], list): return "tool_receipts_not_list"
    if "evidence" in x and not isinstance(x["evidence"], list): return "evidence_not_list"
    return None

ap=argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("report"); a=ap.parse_args()
errors=[]; total=0
for n,line in enumerate(Path(a.input).read_text(encoding="utf-8").splitlines(),1):
    if not line.strip(): continue
    total += 1
    try: err=check(json.loads(line))
    except Exception: err="invalid_json"
    if err: errors.append({"line":n,"error":err})
out={"total":total,"valid":total-len(errors),"invalid":len(errors),"training_eligible":False,"errors":errors}
Path(a.report).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False))
raise SystemExit(1 if errors else 0)
