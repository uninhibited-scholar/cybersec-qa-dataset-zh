#!/bin/bash
# Replays only an already-exposed/rejected v0.9 sample to diagnose empty output.
# This is not blind evaluation, capability scoring, or candidate selection.
#SBATCH --job-name=p108-v09-replay
#SBATCH --partition=GPU-TITANX
#SBATCH --gres=gpu:TITANX:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-v09-replay-%j.log

set -euo pipefail
umask 077
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
SERVER="$ROOT/data/training/phase108_candidate_sandbox_api_smoke_20260926.py"
REPLAY="$ROOT/data/training/phase108_replay_diagnostic.py"
CASES="$ROOT/data/phase108-eval-private-v09/phase108-private-cases-v0.9.json"
RUN_DIR="$ROOT/results/phase108-exposed-replay-$SLURM_JOB_ID"
CASES_SHA=9a4d398893034b922cc67582089642c553733c856ab2812088b398a2546fbb6b
SERVER_SHA=df1484bd0b01ee72e3b41dbb2a7ceda7b384d1e08f99239ffde68357338f83f7
REPLAY_SHA=c4b3744cb951f24c3d51fe087c8fb36b8953e8d7391baf3862967a56508118ea

check_hash() {
  test -r "$1"
  test "$(sha256sum "$1" | awk '{print $1}')" = "$2"
}
check_hash "$CASES" "$CASES_SHA"
check_hash "$SERVER" "$SERVER_SHA"
check_hash "$REPLAY" "$REPLAY_SHA"
test -r "$BASE/config.json"
test ! -e "$RUN_DIR"
mkdir -m 700 "$RUN_DIR"

run_candidate() {
  local name="$1" adapter="$2" expected="$3" port="$4"
  local server_log="$RUN_DIR/server-$name.log" details="$RUN_DIR/details-$name.jsonl"
  local summary="$RUN_DIR/summary-$name.json" pid=""
  check_hash "$adapter" "$expected"
  "$PYTHON" -u "$SERVER" --base "$BASE" --adapter "$adapter" \
    --expected-adapter-sha256 "$expected" --port "$port" --scale 20 \
    >"$server_log" 2>&1 &
  pid=$!
  cleanup() { kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; }
  trap cleanup RETURN
  local deadline=$((SECONDS + 600))
  until curl -fsS --max-time 3 "http://127.0.0.1:$port/health" >/dev/null; do
    kill -0 "$pid" 2>/dev/null || { echo "candidate server failed: $name" >&2; return 1; }
    (( SECONDS < deadline )) || { echo "candidate health timeout: $name" >&2; return 1; }
    sleep 5
  done
  chmod 600 "$server_log"
  "$PYTHON" "$REPLAY" --cases "$CASES" --output "$details" \
    --url "http://127.0.0.1:$port/v1/chat/completions" \
    --expected-cases-sha256 "$CASES_SHA"
  "$PYTHON" - "$details" "$summary" "$name" "$expected" "$CASES_SHA" <<'PY'
import hashlib,json,statistics,sys
from pathlib import Path
src,out,name,adapter_sha,cases_sha=sys.argv[1:]
raw=Path(src).read_bytes(); rows=[json.loads(line) for line in raw.splitlines() if line]
assert len(rows)==16 and all(r.get("blind") is False and r.get("diagnostic_only") is True for r in rows)
result={"diagnostic":"exposed_v0.9_empty_output_replay","blind":False,"capability_score":False,"promotion_eligible":False,"candidate":name,"adapter_sha256":adapter_sha,"case_source_sha256":cases_sha,"cases":len(rows),"empty":sum(bool(r["empty"]) for r in rows),"nonempty":sum(not bool(r["empty"]) for r in rows),"min_chars":min(r["chars"] for r in rows),"max_chars":max(r["chars"] for r in rows),"median_chars":statistics.median(r["chars"] for r in rows),"result_metadata_sha256":hashlib.sha256(raw).hexdigest()}
Path(out).write_text(json.dumps(result,sort_keys=True)+"\n")
Path(out).chmod(0o600)
print(json.dumps(result,sort_keys=True),flush=True)
PY
  chmod 600 "$details"
  cleanup
  trap - RETURN
}

run_candidate formatmix-final \
  "$ROOT/models/phase108-formatmix-20260925/adapters.safetensors" \
  3c87564c97b003990242b988c72cd8c76a9ccf0f8bfbf1058a106f53e26ef461 21830
run_candidate bare-canary-final \
  "$ROOT/models/phase108-bare-canary-20260925/adapters.safetensors" \
  5686ee98e8ed09cd31f3f0228dd4cfec60fd58907090b5ec71372c83571f7da4 21831

echo "exposed_replay_complete=true blind=false candidate_scoring=false production=false raw_text_saved=false run_dir=$RUN_DIR"
