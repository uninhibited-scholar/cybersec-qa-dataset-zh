#!/bin/bash
# Separate, bounded Qwen3-14B service with a transparent Qwen3-1.7B CPU fallback.
# This is a general-model serving/Harness endpoint, not a Phase108 promotion.
# All listeners bind to compute-node loopback; access is through an SSH tunnel.
#SBATCH --job-name=qwen14b-api-service
#SBATCH --partition=GPU-LARGE
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --time=2-00:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/%x-%j.out
#SBATCH --error=/data3/ieug25/zj225/cyber-model-migration/logs/%x-%j.err

set -Eeuo pipefail

ROOT=/data3/ieug25/zj225/cyber-model-migration
MODEL_ROOT=/data3/ieug25/zj225/models
CONDA=/data3/ieug25/zj225/miniforge3/etc/profile.d/conda.sh
MODEL_PATH="$MODEL_ROOT/Qwen3-14B-BF16"
SMALL_MODEL_PATH="$MODEL_ROOT/Qwen3-1.7B"
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python

source "$CONDA"
conda activate coevo
cd "$ROOT"
test -r "$MODEL_PATH/config.json"
test -r "$MODEL_PATH/model.safetensors.index.json"
test -r "$SMALL_MODEL_PATH/config.json"
test -x "$PYTHON"

RUN_DIR="$ROOT/results/qwen14b-api-service-$SLURM_JOB_ID"
test ! -e "$RUN_DIR"
mkdir -m 700 "$RUN_DIR"

PORT_BASE=$((24000 + SLURM_JOB_ID % 10000))
BIG_PORT=$PORT_BASE
SMALL_PORT=$((PORT_BASE + 1))
ROUTER_PORT=$((PORT_BASE + 2))
NODE=$(hostname -s)
MODEL_INDEX_SHA256=$(sha256sum "$MODEL_PATH/model.safetensors.index.json" | awk '{print $1}')
MODEL_CONFIG_SHA256=$(sha256sum "$MODEL_PATH/config.json" | awk '{print $1}')

TMP_DIR=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/qwen14b-smoke.XXXXXX")
chmod 700 "$TMP_DIR"
small_pid=
router_pid=
big_pid=
cleanup() {
  for pid in "$router_pid" "$big_pid" "$small_pid"; do
    if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; fi
  done
  for pid in "$router_pid" "$big_pid" "$small_pid"; do
    if [[ -n "$pid" ]]; then wait "$pid" 2>/dev/null || true; fi
  done
  rm -rf -- "$TMP_DIR"
}
trap cleanup EXIT INT TERM

export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false

SMALL_MODEL_PATH="$SMALL_MODEL_PATH" SMALL_PORT="$SMALL_PORT" \
MODEL_ID=qwen3-1.7b-cpu "$PYTHON" -u data/training/cpu_small_model_server.py \
  >"$RUN_DIR/small.log" 2>&1 &
small_pid=$!

BIG_API="http://127.0.0.1:$BIG_PORT" SMALL_API="http://127.0.0.1:$SMALL_PORT" \
ROUTER_PORT="$ROUTER_PORT" BIG_TIMEOUT_SECONDS=120 \
PUBLIC_MODEL_ID=qwen3-14b-bf16 "$PYTHON" -u data/training/dual_model_router.py \
  >"$RUN_DIR/router.log" 2>&1 &
router_pid=$!

small_ready=0
for _ in $(seq 1 180); do
  if ! kill -0 "$small_pid" 2>/dev/null; then
    echo "service failed: CPU fallback process exited" >&2
    tail -n 40 "$RUN_DIR/small.log" >&2
    exit 1
  fi
  if curl -fsS --max-time 3 "http://127.0.0.1:$SMALL_PORT/health" >"$TMP_DIR/small-health.json" 2>/dev/null && \
     curl -fsS --max-time 3 "http://127.0.0.1:$ROUTER_PORT/health" >"$TMP_DIR/router-health.json" 2>/dev/null; then
    small_ready=1
    break
  fi
  sleep 2
done
if [[ "$small_ready" != 1 ]]; then
  echo "service failed: CPU fallback/router startup timeout" >&2
  tail -n 40 "$RUN_DIR/small.log" "$RUN_DIR/router.log" >&2
  exit 1
fi

# Verify fallback behavior before the large backend starts. The smoke client
# stores only status, route, lengths and timing; response text is not persisted.
"$PYTHON" data/training/dual_model_api_smoke.py \
  --base-url "http://127.0.0.1:$ROUTER_PORT" \
  --expected-route small_fallback --output "$RUN_DIR/fallback-smoke.json"

MODEL_PATH="$MODEL_PATH" MODEL_ID=qwen3-14b-bf16 MODEL_PORT="$BIG_PORT" \
MAX_NEW_TOKENS=512 "$PYTHON" -u data/training/qwen_gpu_model_server.py \
  >"$RUN_DIR/big.log" 2>&1 &
big_pid=$!

big_ready=0
for _ in $(seq 1 600); do
  if ! kill -0 "$big_pid" 2>/dev/null; then
    echo "service failed: Qwen3-14B process exited during load" >&2
    tail -n 60 "$RUN_DIR/big.log" >&2
    exit 1
  fi
  if curl -fsS --max-time 3 "http://127.0.0.1:$BIG_PORT/health" >"$TMP_DIR/big-health.json" 2>/dev/null; then
    big_ready=1
    break
  fi
  sleep 2
done
if [[ "$big_ready" != 1 ]]; then
  echo "service failed: Qwen3-14B startup timeout" >&2
  tail -n 60 "$RUN_DIR/big.log" >&2
  exit 1
fi

# Require real, non-empty big-model output over JSON and SSE before publishing
# the endpoint. Any failure exits the Slurm job and releases its GPU allocation.
"$PYTHON" data/training/dual_model_api_smoke.py \
  --base-url "http://127.0.0.1:$ROUTER_PORT" \
  --expected-route big --output "$RUN_DIR/big-smoke.json"

printf '{"status":"ready","job_id":"%s","node":"%s","bind":"127.0.0.1","router_port":%s,"primary_model":"qwen3-14b-bf16","fallback_model":"qwen3-1.7b-cpu","primary_config_sha256":"%s","primary_index_sha256":"%s","phase108_adapter_loaded":false,"tools":[],"expires_after":"Slurm allocation time limit"}\n' \
  "$SLURM_JOB_ID" "$NODE" "$ROUTER_PORT" "$MODEL_CONFIG_SHA256" "$MODEL_INDEX_SHA256" \
  >"$RUN_DIR/ready.json"
chmod 600 "$RUN_DIR/ready.json" "$RUN_DIR/fallback-smoke.json" "$RUN_DIR/big-smoke.json"
printf 'QWEN14B_API_READY=true node=%s router_port=%s run_dir=%s\n' "$NODE" "$ROUTER_PORT" "$RUN_DIR"
printf 'SSH tunnel template: ssh -N -J zj225@slurmc.ie.cuhk.edu.hk -L 127.0.0.1:19002:127.0.0.1:%s zj225@%s\n' "$ROUTER_PORT" "$NODE"

# Keep the bounded service alive. If any backend/router dies, stop and release
# the allocation rather than silently claiming the intended service is healthy.
while kill -0 "$small_pid" 2>/dev/null && kill -0 "$router_pid" 2>/dev/null && kill -0 "$big_pid" 2>/dev/null; do
  sleep 30
done
echo "service failed: one or more model/router processes exited" >&2
tail -n 40 "$RUN_DIR/small.log" "$RUN_DIR/router.log" "$RUN_DIR/big.log" >&2
exit 1
