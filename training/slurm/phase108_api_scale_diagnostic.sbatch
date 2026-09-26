#!/bin/bash
# Short, isolated loopback API functionality diagnostic; never a production service.
# It tests the exact corrected-r2 final adapter at its recorded scale and a
# separate diagnostic scale. It records metadata only and has no tool access.
#SBATCH --job-name=p108-api-smoke
#SBATCH --partition=test
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-api-smoke-%j.log

set -euo pipefail
umask 077
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
ADAPTER="$ROOT/models/phase108-cuda-recovery-scale20-corrected-20260924-r2/adapters.safetensors"
EXPECTED_ADAPTER_SHA256=4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772
SERVER="$ROOT/data/training/phase108_candidate_sandbox_api_smoke_20260926.py"
SMOKE="$ROOT/data/training/phase108_api_function_smoke_20260926.py"
RUN_DIR="$ROOT/results/phase108-api-scale-diagnostic-$SLURM_JOB_ID"

test -r "$BASE/config.json"
test -r "$ADAPTER"
test -r "$SERVER"
test -r "$SMOKE"
test ! -e "$RUN_DIR"
test "$(sha256sum "$ADAPTER" | awk '{print $1}')" = "$EXPECTED_ADAPTER_SHA256"
mkdir -m 700 "$RUN_DIR"

run_scale() {
  local scale="$1" port="$2" server_pid=""
  local server_log="$RUN_DIR/server-scale-${scale}.log"
  "$PYTHON" -u "$SERVER" --base "$BASE" --adapter "$ADAPTER" \
    --expected-adapter-sha256 "$EXPECTED_ADAPTER_SHA256" \
    --port "$port" --scale "$scale" >"$server_log" 2>&1 &
  server_pid=$!
  cleanup_server() {
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  }
  trap cleanup_server RETURN
  deadline=$((SECONDS + 600))
  until curl -fsS --max-time 3 "http://127.0.0.1:$port/health" >/dev/null; do
    kill -0 "$server_pid" 2>/dev/null || { echo "server failed at scale=$scale" >&2; return 1; }
    (( SECONDS < deadline )) || { echo "health timeout at scale=$scale" >&2; return 1; }
    sleep 5
  done
  chmod 600 "$server_log"
  "$PYTHON" "$SMOKE" --base-url "http://127.0.0.1:$port" \
    --output "$RUN_DIR/smoke-scale-${scale}.json" --scale "$scale"
  chmod 600 "$RUN_DIR/smoke-scale-${scale}.json"
  cleanup_server
  trap - RETURN
}

run_scale 20 21808
run_scale 5 21809
echo "api_scale_diagnostic_complete=true result_dir=$RUN_DIR raw_text_saved=false production_port=false tools=[]"
