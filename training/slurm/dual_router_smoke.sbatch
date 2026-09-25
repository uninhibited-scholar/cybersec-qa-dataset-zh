#!/bin/bash
# Isolated router smoke test; does not touch production port 18765.
#SBATCH --job-name=dual-router-smoke
#SBATCH --partition=GPU-LARGE
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p logs
source /data3/ieug25/zj225/miniforge3/etc/profile.d/conda.sh
conda activate coevo

small_port=19001
router_port=19002
tmpdir=$(mktemp -d)
cleanup() {
  kill "${router_pid:-}" "${small_pid:-}" 2>/dev/null || true
  wait "${router_pid:-}" "${small_pid:-}" 2>/dev/null || true
  rm -rf "$tmpdir"
}
trap cleanup EXIT

SMALL_MODEL_PATH=/data3/ieug25/zj225/models/Qwen3-1.7B \
SMALL_PORT=$small_port \
python data/training/cpu_small_model_server.py >"$tmpdir/small.log" 2>&1 &
small_pid=$!

BIG_API=http://127.0.0.1:19999 \
SMALL_API=http://127.0.0.1:${small_port} \
ROUTER_PORT=$router_port \
BIG_TIMEOUT_SECONDS=3 \
python data/training/dual_model_router.py >"$tmpdir/router.log" 2>&1 &
router_pid=$!

for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${small_port}/health" >/dev/null 2>&1 && \
     curl -fsS "http://127.0.0.1:${router_port}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

curl -fsS "http://127.0.0.1:${router_port}/health"
cat >"$tmpdir/request.json" <<'JSON'
{"model":"router-test","messages":[{"role":"user","content":"Reply with exactly one short sentence confirming the fallback test."}],"max_tokens":32,"temperature":0}
JSON
curl -fsS -D "$tmpdir/router.headers" -H 'Content-Type: application/json' \
  --data-binary "@$tmpdir/request.json" \
  "http://127.0.0.1:${router_port}/v1/chat/completions" | tee "$tmpdir/response.json"
grep -qi 'X-Model-Route: small_fallback' "$tmpdir/router.headers"
grep -q '"choices"' "$tmpdir/response.json"
grep -q '"content": "' "$tmpdir/response.json"
if grep -Eqi '<think>|</think>' "$tmpdir/response.json"; then
  echo "DUAL_ROUTER_SMOKE=FAIL reason=reasoning_channel_leaked"
  exit 1
fi
echo "DUAL_ROUTER_SMOKE=PASS route=small_fallback production_port=18765 untouched"
