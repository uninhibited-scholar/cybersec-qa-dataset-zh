#!/bin/bash
# Standalone CPU fallback.  Deliberately requests no GPU resource.
# It is transparent and bounded; the job is only useful if the cluster
# permits CPU-only work on GPU-LARGE nodes.
#SBATCH --job-name=qwen17b-cpu-fallback
#SBATCH --partition=GPU-LARGE
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=2-00:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/%x-%j.out
#SBATCH --error=/data3/ieug25/zj225/cyber-model-migration/logs/%x-%j.err

set -Eeuo pipefail
ROOT=/data3/ieug25/zj225/cyber-model-migration
MODEL_ROOT=/data3/ieug25/zj225/models
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
source /data3/ieug25/zj225/miniforge3/etc/profile.d/conda.sh
conda activate coevo
cd "$ROOT"

test -r "$MODEL_ROOT/Qwen3-1.7B/config.json"
test -x "$PYTHON"
RUN_DIR="$ROOT/results/qwen17b-cpu-fallback-$SLURM_JOB_ID"
mkdir -m 700 "$RUN_DIR"
PORT_BASE=$((25000 + SLURM_JOB_ID % 10000))
SMALL_PORT=$PORT_BASE
GATEWAY_PORT=$((PORT_BASE + 1))
NODE_IP=$(hostname -I | awk '{print $1}')
TOKEN=${CLUSTER_MODEL_API_TOKEN:?CLUSTER_MODEL_API_TOKEN is required}

cleanup() { [[ -n "${gateway_pid:-}" ]] && kill "$gateway_pid" 2>/dev/null || true; [[ -n "${small_pid:-}" ]] && kill "$small_pid" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

SMALL_MODEL_PATH="$MODEL_ROOT/Qwen3-1.7B" SMALL_PORT="$SMALL_PORT" \
  MODEL_ID=qwen3-1.7b-cpu "$PYTHON" -u data/training/cpu_small_model_server.py \
  >"$RUN_DIR/model.log" 2>&1 &
small_pid=$!
CLUSTER_MODEL_API_TOKEN="$TOKEN" "$PYTHON" -u data/training/cluster_model_api_gateway.py \
  --bind-ip "$NODE_IP" --port "$GATEWAY_PORT" --allowed-source 172.16.5.179 \
  --upstream "http://127.0.0.1:$SMALL_PORT" >"$RUN_DIR/gateway.log" 2>&1 &
gateway_pid=$!

for _ in $(seq 1 300); do
  if ! kill -0 "$small_pid" 2>/dev/null || ! kill -0 "$gateway_pid" 2>/dev/null; then
    tail -n 80 "$RUN_DIR/model.log" "$RUN_DIR/gateway.log" >&2 || true
    exit 1
  fi
  if curl -fsS --max-time 3 "http://127.0.0.1:$SMALL_PORT/health" >/dev/null 2>&1 && \
     curl -fsS --max-time 3 "http://$NODE_IP:$GATEWAY_PORT/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
curl -fsS --max-time 3 "http://127.0.0.1:$SMALL_PORT/health" >"$RUN_DIR/ready.json"
chmod 600 "$RUN_DIR/ready.json"
printf 'QWEN17B_CPU_READY=true job_id=%s node=%s gateway_port=%s\n' "$SLURM_JOB_ID" "$NODE_IP" "$GATEWAY_PORT"
while kill -0 "$small_pid" 2>/dev/null && kill -0 "$gateway_pid" 2>/dev/null; do sleep 30; done
exit 1
