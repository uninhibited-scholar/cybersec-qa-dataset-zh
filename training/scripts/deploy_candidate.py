#!/usr/bin/env python3
"""Explicitly-confirmed, rollback-capable adapter switch.

Default mode is a non-mutating dry run. Production changes require a human
to pass --confirm-production after the approval report is eligible.
"""
import argparse, hashlib, json, shutil, time
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--production',type=Path,required=True)
    ap.add_argument('--approval',type=Path,required=True)
    ap.add_argument('--confirm-production',action='store_true')
    args=ap.parse_args()
    report=json.loads(args.approval.read_text())
    result={'candidate':str(args.candidate),'production':str(args.production),
            'eligible':report.get('eligible') is True,'mutated':False,'mode':'dry-run'}
    if not args.candidate.is_dir() or not args.production.is_dir():
        result['error']='candidate or production directory missing'; print(json.dumps(result,indent=2)); return 2
    if report.get('eligible') is not True:
        result['error']='approval report is not eligible'; print(json.dumps(result,indent=2)); return 2
    if not args.confirm_production:
        result['note']='pass --confirm-production only after human authorization'; print(json.dumps(result,indent=2)); return 0
    backup=args.production.with_name(args.production.name+'.backup-'+time.strftime('%Y%m%d%H%M%S'))
    shutil.copytree(args.production,backup)
    # Copy candidate contents into the production adapter directory only after
    # an explicit confirmation; backup makes rollback recoverable.
    for src in args.candidate.iterdir():
        dst=args.production/src.name
        if src.is_file(): shutil.copy2(src,dst)
    result.update({'mode':'confirmed-switch','backup':str(backup),'mutated':True})
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
