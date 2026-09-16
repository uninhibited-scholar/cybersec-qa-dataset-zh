#!/usr/bin/env python3
"""Non-mutating deployment gate; a candidate can never self-approve."""
import argparse, json
from pathlib import Path
from candidate_manifest import verify as verify_manifest

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--results',type=Path,required=True)
    ap.add_argument('--tool-report',type=Path,required=True)
    ap.add_argument('--trajectory-report',type=Path,required=True,
                    help='Phase 26 offline self-evolution gate report')
    ap.add_argument('--manifest',type=Path,required=True,
                    help='candidate-manifest.json for the evaluated candidate')
    ap.add_argument('--architecture-report',type=Path,required=True,
                    help='base/adapter/Harness separation report')
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--production',type=Path,required=True)
    ap.add_argument('--manual-review',action='store_true')
    args=ap.parse_args()
    reasons=[]
    if not args.candidate.is_dir(): reasons.append('candidate adapter directory missing')
    if not args.production.is_dir(): reasons.append('production adapter rollback source missing')
    try:
        result=json.loads(args.results.read_text())
        tool=json.loads(args.tool_report.read_text())
        trajectory=json.loads(args.trajectory_report.read_text())
        manifest=json.loads(args.manifest.read_text())
        architecture=json.loads(args.architecture_report.read_text())
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        reasons.append(f'gate report unreadable: {type(exc).__name__}')
        result=tool=trajectory=manifest=architecture={}
    if result.get('passes') != result.get('total'): reasons.append('blind suite not fully passed')
    if result.get('forbidden_hits',0): reasons.append('forbidden pattern hit')
    if tool.get('negative_pass') != tool.get('negative_total'): reasons.append('tool negative gate failed')
    if tool.get('positive_pass') != tool.get('positive_total'): reasons.append('tool positive gate failed')
    if tool.get('production_changed'): reasons.append('tool report says production changed')
    if trajectory.get('passed') is not True: reasons.append('self-evolution trajectory gate failed')
    if trajectory.get('production_mutated') is not False: reasons.append('trajectory report says production mutated')
    if trajectory.get('deployment_attempted') is not False: reasons.append('trajectory report attempted deployment')
    if trajectory.get('failures'): reasons.append('trajectory report contains failures')
    if architecture.get('passed') is not True: reasons.append('architecture separation gate failed')
    if architecture.get('production_mutated') is not False: reasons.append('architecture report says production mutated')
    if architecture.get('adapter') != str(args.candidate.resolve()):
        reasons.append('architecture report does not identify this candidate')
    if not architecture.get('base') or not architecture.get('harness'):
        reasons.append('architecture report missing base or Harness identity')
    manifest_errors = verify_manifest(args.candidate, manifest)
    if manifest_errors: reasons.extend(f'manifest: {item}' for item in manifest_errors)
    if not args.manual_review: reasons.append('independent manual review not recorded')
    decision={'candidate':str(args.candidate),'eligible':not reasons,'reasons':reasons,'mutated':False}
    print(json.dumps(decision,ensure_ascii=False,indent=2))
    raise SystemExit(0 if not reasons else 2)
if __name__=='__main__': main()
