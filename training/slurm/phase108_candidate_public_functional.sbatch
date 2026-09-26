#!/bin/bash
# Public development-only empty-output/API compatibility screen.
# No blind-suite, production API, tools, weights, or serving endpoint changes.
#SBATCH --job-name=p108-pub-fn
#SBATCH --partition=GPU-TITANX
#SBATCH --gres=gpu:TITANX:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:45:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-public-functional-%j.log

set -euo pipefail
umask 077
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
SERVER="$ROOT/data/training/phase108_candidate_sandbox_api_smoke_20260926.py"
CLIENT="$ROOT/data/training/phase108_candidate_public_functional_20260926.py"
RUN_DIR="$ROOT/results/phase108-public-functional-$SLURM_JOB_ID"

test -r "$BASE/config.json"
test -r "$SERVER"
test -r "$CLIENT"
test ! -e "$RUN_DIR"
mkdir -m 700 "$RUN_DIR"

run_candidate() {
  local name="$1" adapter="$2" expected="$3" port="$4" scale=20
  local log="$RUN_DIR/server-${name}.log" pid=""
  test -r "$adapter"
  test "$(sha256sum "$adapter" | awk '{print $1}')" = "$expected"
  "$PYTHON" -u "$SERVER" --base "$BASE" --adapter "$adapter" \
    --expected-adapter-sha256 "$expected" --port "$port" --scale "$scale" \
    >"$log" 2>&1 &
  pid=$!
  cleanup() { kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; }
  trap cleanup RETURN
  local deadline=$((SECONDS + 600))
  until curl -fsS --max-time 3 "http://127.0.0.1:$port/health" >/dev/null; do
    kill -0 "$pid" 2>/dev/null || { echo "server failed for $name" >&2; return 1; }
    (( SECONDS < deadline )) || { echo "health timeout for $name" >&2; return 1; }
    sleep 5
  done
  chmod 600 "$log"
  "$PYTHON" "$CLIENT" --base-url "http://127.0.0.1:$port" --scale "$scale" \
    --adapter-sha256 "$expected" --output "$RUN_DIR/${name}.json"
  chmod 600 "$RUN_DIR/${name}.json"
  cleanup
  trap - RETURN
}

run_candidate formatmix \
  "$ROOT/models/phase108-formatmix-20260925/adapters.safetensors" \
  3c87564c97b003990242b988c72cd8c76a9ccf0f8bfbf1058a106f53e26ef461 21820
run_candidate bare-canary \
  "$ROOT/models/phase108-bare-canary-20260925/adapters.safetensors" \
  5686ee98e8ed09cd31f3f0228dd4cfec60fd58907090b5ec71372c83571f7da4 21821

echo "public_functional_complete=true job=$SLURM_JOB_ID blind=false production=false tools=[] raw_prompts_saved=false raw_responses_saved=false"
