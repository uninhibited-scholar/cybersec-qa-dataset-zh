#!/usr/bin/env bash
# Loopback-only API compatibility smoke with synthetic, non-benchmark text.
# No API is exposed off-node; no tools or private evaluation cases are used.
#SBATCH --job-name=p107-api-smoke
#SBATCH --partition=GPU-LARGE
#SBATCH --gres=gpu:A100-40G:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:12:00
#SBATCH --output=phase107-api-smoke-%j.out

set -euo pipefail

readonly ROOT="$HOME/cyber-model-migration/phase107-runtime"
readonly SERVER="$ROOT/llama-b11046-cuda-12.8-x64/llama-b11046/llama-server"
readonly MODEL="$ROOT/models/gpt-oss-20b-UD-Q4_K_XL.gguf"
readonly CUDA_LIB_ROOT="$HOME/miniforge3/envs/cyber-cuda/lib/python3.11/site-packages/nvidia"
readonly PORT=18877

CUDA_LIB_PATH=""
for libdir in "$CUDA_LIB_ROOT"/*/lib; do
  if [[ -d "$libdir" ]]; then
    CUDA_LIB_PATH="${CUDA_LIB_PATH:+$CUDA_LIB_PATH:}$libdir"
  fi
done
export LD_LIBRARY_PATH="${CUDA_LIB_PATH}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

test -x "$SERVER"
test -f "$MODEL"
echo "timestamp=$(date -Is) host=$(hostname) gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)"

"$SERVER" \
  --model "$MODEL" \
  --host 127.0.0.1 \
  --port "$PORT" \
  --cors-origins localhost \
  --ctx-size 4096 \
  --n-gpu-layers 999 \
  --no-webui \
  --reasoning auto \
  --temp 0.12 \
  --top-p 0.9 \
  --top-k 0 \
  --min-p 0 \
  --repeat-penalty 1.12 \
  --repeat-last-n 128 \
  --seed 107 &
SERVER_PID=$!
cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

ready=0
for _ in $(seq 1 120); do
  if curl -fsS --max-time 2 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    ready=1
    break
  fi
  kill -0 "$SERVER_PID" 2>/dev/null || { echo "server exited before readiness" >&2; exit 2; }
  sleep 2
done
test "$ready" -eq 1 || { echo "server readiness timeout" >&2; exit 3; }

response="$(curl -fsS --max-time 180 "http://127.0.0.1:$PORT/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "model": "reference-smoke",
  "max_tokens": 64,
  "messages": [
    {"role": "system", "content": "Follow the user's request exactly."},
    {"role": "user", "content": "The temporary test code is 4f2a. Remember it."},
    {"role": "assistant", "content": "Acknowledged."},
    {"role": "user", "content": "Repeat the temporary test code only."}
  ]
}
JSON
)"

python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); c=d["choices"][0]; m=c["message"]; s=m.get("content") or ""; assert "4f2a" in s, "multi-turn content check failed"; print("api_schema=pass choices=1 finish_reason="+str(c.get("finish_reason"))+" multi_turn_context=pass tools=none")' <<<"$response"
echo "smoke_exit=0"
