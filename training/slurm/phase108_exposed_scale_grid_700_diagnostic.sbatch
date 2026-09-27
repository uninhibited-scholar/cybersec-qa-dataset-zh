#!/bin/bash
# Exposed-only scale/termination diagnostic for the Phase108 HF adapter path.
# Not a blind evaluation, capability score, scale selection, or promotion gate.
# It stores per-case hashes/lengths/finish reasons only, never prompts/answers.
#SBATCH --job-name=p108-scalegrid-700
#SBATCH --partition=GPU-TITANX
#SBATCH --gres=gpu:TITANX:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-scalegrid-700-%j.log
#SBATCH --error=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-scalegrid-700-%j.err

set -euo pipefail
umask 077

ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
SERVER="$ROOT/data/training/phase108_candidate_sandbox_api_scale_diag.py"
REPLAY="$ROOT/data/training/phase108_greedy_exposed_replay.py"
CASES="$ROOT/data/phase108-eval-private-v09/phase108-private-cases-v0.9.json"
PARENT="$ROOT/models/phase108-step12000-20260920/0012000_adapters.safetensors"
CANDIDATE="$ROOT/models/phase108-cuda-recovery-scale20-corrected-20260924-r2/adapters.safetensors"
RUN_DIR="$ROOT/results/phase108-exposed-scale-grid-700-$SLURM_JOB_ID"

readonly CASES_SHA=9a4d398893034b922cc67582089642c553733c856ab2812088b398a2546fbb6b
readonly SERVER_SHA=df1484bd0b01ee72e3b41dbb2a7ceda7b384d1e08f99239ffde68357338f83f7
readonly REPLAY_SHA=f503bc795cb7ad3dee3d88bf09f7527aec06261ce43a1fb8c966a7f66c59b6f1
readonly BASE_CONFIG_SHA=260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650
readonly BASE_INDEX_SHA=5e699a61da09415f33a625885364d3889a80acb6ab88aedaf6e195b2612addf4
readonly BASE_SHARD1_SHA=25094f7fbaef4769da447cb6ebf4a39d99ccc5043856cce1b4f8fc2f91ed9115
readonly BASE_SHARD2_SHA=a2fd70328fc4fb518bb40ac806e8c05f21ad12e228648684775f67c28104815d
readonly PARENT_SHA=3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036
readonly CANDIDATE_SHA=4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772

check_hash() {
  local path="$1" expected="$2" actual
  test -r "$path"
  actual=$(sha256sum "$path" | awk '{print $1}')
  test "$actual" = "$expected"
}

check_hash "$CASES" "$CASES_SHA"
check_hash "$SERVER" "$SERVER_SHA"
check_hash "$REPLAY" "$REPLAY_SHA"
check_hash "$BASE/config.json" "$BASE_CONFIG_SHA"
check_hash "$BASE/model.safetensors.index.json" "$BASE_INDEX_SHA"
check_hash "$BASE/model-00001-of-00002.safetensors" "$BASE_SHARD1_SHA"
check_hash "$BASE/model-00002-of-00002.safetensors" "$BASE_SHARD2_SHA"
check_hash "$PARENT" "$PARENT_SHA"
check_hash "$CANDIDATE" "$CANDIDATE_SHA"
test ! -e "$RUN_DIR"
mkdir -m 700 "$RUN_DIR"
JOB_SHA=$(sha256sum "$0" | awk '{print $1}')
REPLAY_LOCAL_SHA=$(sha256sum "$REPLAY" | awk '{print $1}')
test "$REPLAY_LOCAL_SHA" = "$REPLAY_SHA"

run_arm() {
  local name="$1" adapter="$2" adapter_sha="$3" scale="$4" port="$5"
  local server_log="$RUN_DIR/server-$name.log"
  local details="$RUN_DIR/details-$name.jsonl"
  local summary="$RUN_DIR/summary-$name.json"
  check_hash "$adapter" "$adapter_sha"
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
    --base-index-sha256 "$BASE_INDEX_SHA" --max-tokens 700
  chmod 600 "$details" "$summary"
  cleanup
  trap - RETURN
}

echo "DIAGNOSTIC_ONLY=true blind=false capability_score=false scale_selection=false promotion=false max_tokens=700 job_script_sha256=$JOB_SHA"
run_arm base-control "$PARENT" "$PARENT_SHA" 0.0 21850
run_arm parent-s2p5 "$PARENT" "$PARENT_SHA" 2.5 21851
run_arm parent-s5 "$PARENT" "$PARENT_SHA" 5.0 21852
run_arm parent-s10 "$PARENT" "$PARENT_SHA" 10.0 21853
run_arm parent-s20 "$PARENT" "$PARENT_SHA" 20.0 21854
run_arm candidate-s2p5 "$CANDIDATE" "$CANDIDATE_SHA" 2.5 21855
run_arm candidate-s5 "$CANDIDATE" "$CANDIDATE_SHA" 5.0 21856
run_arm candidate-s10 "$CANDIDATE" "$CANDIDATE_SHA" 10.0 21857
run_arm candidate-s20 "$CANDIDATE" "$CANDIDATE_SHA" 20.0 21858

echo "scale_grid_diagnostic_complete=true job=$SLURM_JOB_ID blind=false capability_score=false scale_selection=false promotion=false raw_text_saved=false run_dir=$RUN_DIR"
