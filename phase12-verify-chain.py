#!/usr/bin/env python3
import argparse, hashlib, json

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("log"); a=ap.parse_args(); prev="0"*64; n=0
    for line in open(a.log, encoding="utf-8"):
        if not line.strip(): continue
        e=json.loads(line); saved=e.pop("hash", None)
        if e.get("prev_hash") != prev: raise SystemExit(f"broken chain at {n+1}")
        got=hashlib.sha256(json.dumps(e, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if got != saved: raise SystemExit(f"hash mismatch at {n+1}")
        prev=saved; n+=1
    print(f"phase12 chain verification: {n}/{n} events valid")

if __name__ == "__main__": main()
