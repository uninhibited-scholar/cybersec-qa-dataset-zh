#!/bin/bash
# Full-length functional follow-up on a previously exposed Phase108 sample.
# Not blind, not scored, and not a model-selection or promotion gate.
# The scale-0 arm is the no-adapter-equivalent baseline; no text is persisted.
#SBATCH --job-name=p108-scale5-diag
#SBATCH --partition=GPU-TITANX
#SBATCH --gres=gpu:TITANX:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:45:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-scale5-diag-%j.log

set -euo pipefail
umask 077
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
SERVER="$ROOT/data/training/phase108_candidate_sandbox_api.py"
REPLAY="$ROOT/data/training/phase108_greedy_exposed_replay.py"
CASES="$ROOT/data/phase108-eval-private-v09/phase108-private-cases-v0.9.json"
RUN_DIR="$ROOT/results/phase108-exposed-scale5-$SLURM_JOB_ID"
readonly CASES_SHA=9a4d398893034b922cc67582089642c553733c856ab2812088b398a2546fbb6b
readonly SERVER_SHA=df1484bd0b01ee72e3b41dbb2a7ceda7b384d1e08f99239ffde68357338f83f7
readonly BASE_CONFIG_SHA=260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650
readonly BASE_INDEX_SHA=5e699a61da09415f33a625885364d3889a80acb6ab88aedaf6e195b2612addf4

for path in "$BASE/config.json" "$BASE/model.safetensors.index.json" "$SERVER" "$REPLAY" "$CASES"; do test -r "$path"; done
test "$(sha256sum "$CASES" | awk '{print $1}')" = "$CASES_SHA"
test "$(sha256sum "$SERVER" | awk '{print $1}')" = "$SERVER_SHA"
test "$(sha256sum "$BASE/config.json" | awk '{print $1}')" = "$BASE_CONFIG_SHA"
test "$(sha256sum "$BASE/model.safetensors.index.json" | awk '{print $1}')" = "$BASE_INDEX_SHA"
test ! -e "$RUN_DIR"
mkdir -m 700 "$RUN_DIR"
REPLAY_SHA=$(sha256sum "$REPLAY" | awk '{print $1}')
JOB_SHA=$(sha256sum "$0" | awk '{print $1}')

run_arm() {
  local name="$1" adapter="$2" adapter_sha="$3" scale="$4" port="$5"
  local server_log="$RUN_DIR/server-$name.log"
  local details="$RUN_DIR/details-$name.jsonl"
  local summary="$RUN_DIR/summary-$name.json"
  test "$(sha256sum "$adapter" | awk '{print $1}')" = "$adapter_sha"
  "$PYTHON" -u "$SERVER" --base "$BASE" --adapter "$adapter" \
    --expected-adapter-sha256 "$adapter_sha" --port "$port" --scale "$scale" \
    >"$server_log" 2>&1 &
  local server_pid=$!
  cleanup() { kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; }
  trap cleanup RETURN
  local deadline=$((SECONDS + 600))
  until curl -fsS --max-time 3 "http://127.0.0.1:$port/health" >/dev/null; do
    kill -0 "$server_pid" 2>/dev/null || { echo "sandbox failed: $name" >&2; return 1; }
    (( SECONDS < deadline )) || { echo "sandbox health timeout: $name" >&2; return 1; }
    sleep 5
  done
  chmod 600 "$server_log"
  "$PYTHON" "$REPLAY" \
    --cases "$CASES" --expected-cases-sha256 "$CASES_SHA" \
    --url "http://127.0.0.1:$port/v1/chat/completions" \
    --details "$details" --summary "$summary" --candidate "$name" --scale "$scale" \
    --adapter "$adapter" --server "$SERVER" --job-script "$0" --base "$BASE" \
    --adapter-sha256 "$adapter_sha" --server-sha256 "$SERVER_SHA" \
    --replay-sha256 "$REPLAY_SHA" --base-config-sha256 "$BASE_CONFIG_SHA" \
    --base-index-sha256 "$BASE_INDEX_SHA" --max-tokens 128
  chmod 600 "$details" "$summary"
  cleanup
  trap - RETURN
}

PARENT="$ROOT/models/phase108-step12000-20260920/0012000_adapters.safetensors"
R2="$ROOT/models/phase108-cuda-recovery-scale20-corrected-20260924-r2/adapters.safetensors"
PARENT_SHA=3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036
R2_SHA=4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772

# Each request is an already-exposed v0.9 diagnostic case, not fresh blind data.
run_arm base-control "$PARENT" "$PARENT_SHA" 0.0 21832
run_arm parent-scale5 "$PARENT" "$PARENT_SHA" 5.0 21833
run_arm corrected-r2-scale5 "$R2" "$R2_SHA" 5.0 21834

echo "exposed_scale5_diagnostic_complete=true job=$SLURM_JOB_ID arms=3 blind=false capability_score=false promotion=false raw_text_saved=false run_dir=$RUN_DIR"
