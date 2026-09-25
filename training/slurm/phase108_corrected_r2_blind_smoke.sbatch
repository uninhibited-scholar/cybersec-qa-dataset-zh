#!/bin/bash
# Isolated blind smoke collection for corrected-r2. No production access.
# Prompts are selected inside the job; scheduler logs never contain text.
#SBATCH --job-name=phase108-r2-blind
#SBATCH --partition=GPU-MEDIUM
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-r2-blind-%j.log
set -euo pipefail
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
ADAPTER="$ROOT/models/phase108-cuda-recovery-scale20-corrected-20260924-r2/0007000_adapters.safetensors"
SHA=62acbdc57011ea5a4927514c6868549d98ae36501ddbefab847424cb4ebe66ed
SERVER="$ROOT/data/training/phase108_candidate_sandbox_api.py"
CASES="$ROOT/data/phase108-eval-private-v09/phase108-private-cases-v0.9.json"
OUT="$ROOT/results/phase108-r2-blind-$SLURM_JOB_ID.jsonl"
PORT=21829
test "$(sha256sum "$ADAPTER" | awk '{print $1}')" = "$SHA"
test -r "$CASES"
mkdir -p "$ROOT/results"
export PYTHONPATH="$ROOT/data/training"
"$PYTHON" -u "$SERVER" --base "$BASE" --adapter "$ADAPTER" --expected-adapter-sha256 "$SHA" --port "$PORT" >"$ROOT/results/phase108-r2-server-$SLURM_JOB_ID.log" 2>&1 &
PID=$!
trap 'kill "$PID" 2>/dev/null || true' EXIT
for _ in $(seq 1 180); do curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null && break; sleep 5; done
curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null
CASES="$CASES" OUT="$OUT" PORT="$PORT" "$PYTHON" - <<'PY'
import hashlib, json, os, random, urllib.request
rows=json.load(open(os.environ['CASES']))
rng=random.Random(20260925)
chosen=rng.sample(rows, 16)
out=open(os.environ['OUT'],'w')
for row in chosen:
    payload=json.dumps({'messages':row['messages'],'temperature':0.12,'max_tokens':500},ensure_ascii=False).encode()
    req=urllib.request.Request(f"http://127.0.0.1:{os.environ['PORT']}/v1/chat/completions",data=payload,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=180) as resp: body=json.load(resp)
    text=body['choices'][0]['message']['content']
    out.write(json.dumps({'case_id':row['id'],'response_sha256':hashlib.sha256(text.encode()).hexdigest(),'chars':len(text),'empty':not bool(text.strip())})+'\n'); out.flush()
out.close()
print(json.dumps({'status':'blind_smoke_complete','cases':16,'output':os.environ['OUT']}))
PY
