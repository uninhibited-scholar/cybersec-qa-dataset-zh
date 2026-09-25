#!/bin/bash
# End-to-end isolated API smoke: Qwen3-14B BF16 on GPU plus CPU fallback.
# Binds services to loopback on the allocated compute node only.
#SBATCH --job-name=qwen14b-dual-api
#SBATCH --partition=GPU-LARGE
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/%x-%j.out
#SBATCH --error=/data3/ieug25/zj225/cyber-model-migration/logs/%x-%j.err

set -euo pipefail
cd /data3/ieug25/zj225/cyber-model-migration
source /data3/ieug25/zj225/miniforge3/etc/profile.d/conda.sh
conda activate coevo

tmpdir=$(mktemp -d)
port_base=$((25000 + SLURM_JOB_ID % 10000))
big_port=$port_base
small_port=$((port_base + 1))
router_port=$((port_base + 2))
cleanup() {
  kill "${router_pid:-}" "${small_pid:-}" "${big_pid:-}" 2>/dev/null || true
  wait "${router_pid:-}" "${small_pid:-}" "${big_pid:-}" 2>/dev/null || true
  rm -rf "$tmpdir"
}
trap cleanup EXIT

SMALL_MODEL_PATH=/data3/ieug25/zj225/models/Qwen3-1.7B SMALL_PORT=$small_port \
  python data/training/cpu_small_model_server.py >"$tmpdir/small.log" 2>&1 &
small_pid=$!
BIG_API=http://127.0.0.1:${big_port} SMALL_API=http://127.0.0.1:${small_port} \
  ROUTER_PORT=$router_port BIG_TIMEOUT_SECONDS=120 \
  python data/training/dual_model_router.py >"$tmpdir/router.log" 2>&1 &
router_pid=$!

for _ in $(seq 1 90); do
  if curl -fsS "http://127.0.0.1:${small_port}/health" >/dev/null 2>&1 && \
     curl -fsS "http://127.0.0.1:${router_port}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

# Verify fallback while the large model is absent.
cat >"$tmpdir/request.json" <<'JSON'
{"model":"qwen3-14b-bf16","messages":[{"role":"user","content":"Reply with exactly one short sentence confirming the model endpoint is responding."}],"max_tokens":32,"temperature":0,"stream":true}
JSON
curl -fsS -D "$tmpdir/fallback.headers" -H 'Content-Type: application/json' --data-binary "@$tmpdir/request.json" \
  "http://127.0.0.1:${router_port}/v1/chat/completions" >"$tmpdir/fallback.json"
curl -fsS "http://127.0.0.1:${router_port}/v1/models" >"$tmpdir/models.json"
grep -q 'qwen3-14b-bf16' "$tmpdir/models.json"
grep -qi 'X-Model-Route: small_fallback' "$tmpdir/fallback.headers"
grep -q '"choices"' "$tmpdir/fallback.json"
grep -q '"content":' "$tmpdir/fallback.json"
grep -q 'data: \[DONE\]' "$tmpdir/fallback.json"
if grep -Eqi '<think>|</think>' "$tmpdir/fallback.json"; then
  echo "DUAL_API_SMOKE=FAIL reason=fallback_reasoning_leak"
  exit 1
fi

# Start Qwen3-14B BF16 and wait for its health endpoint.
MODEL_PATH=/data3/ieug25/zj225/models/Qwen3-14B-BF16 MODEL_ID=qwen3-14b-bf16 MODEL_PORT=$big_port \
  python data/training/qwen_gpu_model_server.py >"$tmpdir/big.log" 2>&1 &
big_pid=$!
ready=0
for _ in $(seq 1 480); do
  if ! kill -0 "$big_pid" 2>/dev/null; then
    echo "DUAL_API_SMOKE=FAIL reason=big_backend_exited"
    tail -n 30 "$tmpdir/big.log"
    exit 1
  fi
  if curl -fsS "http://127.0.0.1:${big_port}/health" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
if [[ "$ready" != 1 ]]; then
  echo "DUAL_API_SMOKE=FAIL reason=big_backend_start_timeout"
  tail -n 30 "$tmpdir/big.log"
  exit 1
fi

curl -fsS -D "$tmpdir/big.headers" -H 'Content-Type: application/json' --data-binary "@$tmpdir/request.json" \
  "http://127.0.0.1:${router_port}/v1/chat/completions" >"$tmpdir/big.json"
grep -qi 'X-Model-Route: big' "$tmpdir/big.headers"
grep -q '"choices"' "$tmpdir/big.json"
grep -q '"content":' "$tmpdir/big.json"
grep -q 'data: \[DONE\]' "$tmpdir/big.json"
if grep -Eqi '<think>|</think>' "$tmpdir/big.json"; then
  echo "DUAL_API_SMOKE=FAIL reason=big_reasoning_leak"
  exit 1
fi
echo "DUAL_API_SMOKE=PASS fallback=small_fallback big=qwen3-14b-bf16 production_port=18765 untouched"
