#!/bin/bash
# Reproduce a previously exposed 16-case empty-output diagnostic only.
# This is not blind, not scored, and not a promotion gate.
# Raw prompts/answers are never written to logs or output files.
#SBATCH --job-name=p108-replay-empty
#SBATCH --partition=GPU-MEDIUM
#SBATCH --gres=gpu:RTX-3090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-replay-empty-%j.log

set -euo pipefail
umask 077
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
PARENT="$ROOT/models/phase108-step12000-20260920/0012000_adapters.safetensors"
CANDIDATE="$ROOT/models/phase108-cuda-recovery-scale20-corrected-20260924-r2/adapters.safetensors"
CASES="$ROOT/data/phase108-eval-private-v09/phase108-private-cases-v0.9.json"
SERVER="$ROOT/data/training/phase108_candidate_sandbox_api.py"
REPLAY="$ROOT/data/training/phase108_replay_diagnostic.py"
HELPER="$ROOT/data/training/phase108_hf_adapter_smoke.py"
RUN_DIR="$ROOT/results/phase108-v09-replay-$SLURM_JOB_ID"

readonly CASES_SHA256=9a4d398893034b922cc67582089642c553733c856ab2812088b398a2546fbb6b
readonly PARENT_SHA256=3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036
readonly CANDIDATE_SHA256=4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772
readonly SERVER_SHA256=fbae10cc6a253eb4f5d82aed75e0e85e46a2ee4df3c02f59996433eaf52dcb22
readonly REPLAY_SHA256=c4b3744cb951f24c3d51fe087c8fb36b8953e8d7391baf3862967a56508118ea
readonly HELPER_SHA256=00ef5d3b1aaada8285b711a68f47c9e00a4fb9dbbd993e8eaf8eefd7426fa371

for path in "$BASE/config.json" "$PARENT" "$CANDIDATE" "$CASES" "$SERVER" "$REPLAY" "$HELPER"; do test -r "$path"; done
test "$(sha256sum "$PARENT" | awk '{print $1}')" = "$PARENT_SHA256"
test "$(sha256sum "$CANDIDATE" | awk '{print $1}')" = "$CANDIDATE_SHA256"
test "$(sha256sum "$CASES" | awk '{print $1}')" = "$CASES_SHA256"
test "$(sha256sum "$SERVER" | awk '{print $1}')" = "$SERVER_SHA256"
test "$(sha256sum "$REPLAY" | awk '{print $1}')" = "$REPLAY_SHA256"
test "$(sha256sum "$HELPER" | awk '{print $1}')" = "$HELPER_SHA256"
"$PYTHON" -m py_compile "$REPLAY" "$SERVER" "$HELPER"
"$PYTHON" "$REPLAY" --cases "$CASES" --expected-cases-sha256 "$CASES_SHA256" --preflight-only
test ! -e "$RUN_DIR"
mkdir -m 700 "$RUN_DIR"

server_pid=
cleanup() {
  if [[ -n "${server_pid:-}" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

run_arm() {
  local label="$1" adapter="$2" adapter_sha="$3" port="$4"
  "$PYTHON" -u "$SERVER" --base "$BASE" --adapter "$adapter" \
    --expected-adapter-sha256 "$adapter_sha" --port "$port" --scale 20 \
    >"$RUN_DIR/server-$label.log" 2>&1 &
  server_pid=$!
  local ready=false
  for _ in $(seq 1 180); do
    if curl -fsS --max-time 3 "http://127.0.0.1:$port/health" >/dev/null; then
      ready=true; break
    fi
    kill -0 "$server_pid" 2>/dev/null || { echo "server_failed arm=$label"; tail -n 20 "$RUN_DIR/server-$label.log"; return 1; }
    sleep 5
  done
  test "$ready" = true || { echo "server_health_timeout arm=$label"; return 1; }
  "$PYTHON" "$REPLAY" --cases "$CASES" --expected-cases-sha256 "$CASES_SHA256" \
    --url "http://127.0.0.1:$port/v1/chat/completions" \
    --output "$RUN_DIR/$label.jsonl"
  chmod 600 "$RUN_DIR/$label.jsonl" "$RUN_DIR/server-$label.log"
  kill "$server_pid" 2>/dev/null || true
  wait "$server_pid" 2>/dev/null || true
  server_pid=
  sleep 3
}

echo "REPLAY_DIAGNOSTIC_ONLY=true blind=false score=false promotion=false tools=[]"
echo "cases_sha256=$CASES_SHA256 parent_sha256=$PARENT_SHA256 candidate_sha256=$CANDIDATE_SHA256"
run_arm parent "$PARENT" "$PARENT_SHA256" 21831
run_arm candidate "$CANDIDATE" "$CANDIDATE_SHA256" 21832
sha256sum "$RUN_DIR"/parent.jsonl "$RUN_DIR"/candidate.jsonl >"$RUN_DIR/output-sha256.txt"
chmod 600 "$RUN_DIR/output-sha256.txt"
echo "REPLAY_COMPLETE=true output_dir=$RUN_DIR"
