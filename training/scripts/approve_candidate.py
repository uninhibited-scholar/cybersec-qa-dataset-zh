#!/usr/bin/env python3
"""Non-mutating deployment gate; a candidate can never self-approve."""
import argparse, json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--results',type=Path,required=True)
    ap.add_argument('--tool-report',type=Path,required=True)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--production',type=Path,required=True)
    ap.add_argument('--manual-review',action='store_true')
    args=ap.parse_args()
    reasons=[]
    if not args.candidate.is_dir(): reasons.append('candidate adapter directory missing')
    if not args.production.is_dir(): reasons.append('production adapter rollback source missing')
    result=json.loads(args.results.read_text()); tool=json.loads(args.tool_report.read_text())
    if result.get('passes') != result.get('total'): reasons.append('blind suite not fully passed')
    if result.get('forbidden_hits',0): reasons.append('forbidden pattern hit')
    if tool.get('negative_pass') != tool.get('negative_total'): reasons.append('tool negative gate failed')
    if tool.get('positive_pass') != tool.get('positive_total'): reasons.append('tool positive gate failed')
    if tool.get('production_changed'): reasons.append('tool report says production changed')
    if not args.manual_review: reasons.append('independent manual review not recorded')
    decision={'candidate':str(args.candidate),'eligible':not reasons,'reasons':reasons,'mutated':False}
    print(json.dumps(decision,ensure_ascii=False,indent=2))
    raise SystemExit(0 if not reasons else 2)
if __name__=='__main__': main()
