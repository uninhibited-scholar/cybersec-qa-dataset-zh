#!/bin/bash
# Start the exact corrected-r2 adapter in an isolated loopback-only Slurm job,
# then run one metadata-only API smoke. This is not blind capability evidence.
# No production API, adapter, rubric/protocol, tools, or weights are modified.
#SBATCH --job-name=p108-r2-sandbox
#SBATCH --partition=GPU-MEDIUM
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-r2-sandbox-%j.log

set -euo pipefail
umask 077
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
ADAPTER="$ROOT/models/phase108-cuda-recovery-scale20-corrected-20260924-r2/adapters.safetensors"
SERVER="$ROOT/data/training/phase108_candidate_sandbox_api_corrected_r2_20260926.py"
LOADER="$ROOT/data/training/phase108_hf_adapter_smoke.py"
SMOKE="$ROOT/data/training/phase108_api_function_smoke_corrected_r2_20260926.py"
EXPECTED_ADAPTER_SHA256=4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772
EXPECTED_SERVER_SHA256=df1484bd0b01ee72e3b41dbb2a7ceda7b384d1e08f99239ffde68357338f83f7
EXPECTED_LOADER_SHA256=00ef5d3b1aaada8285b711a68f47c9e00a4fb9dbbd993e8eaf8eefd7426fa371
EXPECTED_SMOKE_SHA256=b1ac9d684a3e0efa3d445fe67c779fd1fafa73fcc62cc9944a44fcd511b909b2
EXPECTED_BASE_CONFIG_SHA256=260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650
EXPECTED_BASE_INDEX_SHA256=5e699a61da09415f33a625885364d3889a80acb6ab88aedaf6e195b2612addf4
SCALE=20.0
PORT=$((20000 + SLURM_JOB_ID % 10000))
RUN_DIR="$ROOT/results/phase108-corrected-r2-sandbox-$SLURM_JOB_ID"

check_hash() {
  local path="$1" expected="$2"
  test -r "$path"
  test "$(sha256sum "$path" | awk '{print $1}')" = "$expected"
}

test -r "$BASE/config.json"
test -r "$BASE/model.safetensors.index.json"
check_hash "$BASE/config.json" "$EXPECTED_BASE_CONFIG_SHA256"
check_hash "$BASE/model.safetensors.index.json" "$EXPECTED_BASE_INDEX_SHA256"
check_hash "$ADAPTER" "$EXPECTED_ADAPTER_SHA256"
check_hash "$SERVER" "$EXPECTED_SERVER_SHA256"
check_hash "$LOADER" "$EXPECTED_LOADER_SHA256"
check_hash "$SMOKE" "$EXPECTED_SMOKE_SHA256"
test ! -e "$RUN_DIR"
mkdir -m 700 "$RUN_DIR"

server_pid=""
cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

"$PYTHON" -u "$SERVER" --base "$BASE" --adapter "$ADAPTER" \
  --expected-adapter-sha256 "$EXPECTED_ADAPTER_SHA256" --port "$PORT" \
  --scale "$SCALE" >"$RUN_DIR/server.log" 2>&1 &
server_pid=$!

deadline=$((SECONDS + 600))
until curl -fsS --max-time 3 "http://127.0.0.1:$PORT/health" >"$RUN_DIR/health.json"; do
  kill -0 "$server_pid" 2>/dev/null || { echo "candidate server exited before health" >&2; exit 1; }
  (( SECONDS < deadline )) || { echo "candidate server health timeout" >&2; exit 1; }
  sleep 5
done
chmod 600 "$RUN_DIR/health.json" "$RUN_DIR/server.log"

"$PYTHON" "$SMOKE" --base-url "http://127.0.0.1:$PORT" \
  --output "$RUN_DIR/smoke.json" --scale "$SCALE"
chmod 600 "$RUN_DIR/smoke.json"
check_hash "$ADAPTER" "$EXPECTED_ADAPTER_SHA256"
echo "sandbox_smoke_complete=true blind=false capability_score=false promotion_eligible=false production=false adapter_sha256=$EXPECTED_ADAPTER_SHA256 scale=$SCALE run_dir=$RUN_DIR"
