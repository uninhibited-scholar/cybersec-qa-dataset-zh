#!/usr/bin/env bash
# CPU-only Phase 107 reference servers on the runtime-validated A100-3 host.
# Models, GGUF quantization, native templates, prompts, sampling, and tools are
# unchanged; this uses CPU inference while the A100 queue is delayed.
#SBATCH --job-name=phase107-cpu-refs
#SBATCH --partition=GPU-LARGE
#SBATCH --nodelist=a100-3
#SBATCH --cpus-per-task=12
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH --output=logs/phase107-cpu-refs-%j.out

set -euo pipefail
readonly ROOT="$HOME/cyber-model-migration/phase107-runtime"
readonly RUNTIME="$ROOT/llama-b11046-cuda-12.8-x64/llama-b11046"
readonly MODEL_DIR="$ROOT/models"
readonly LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"
cuda_lib_path=""
for libdir in "$HOME"/miniforge3/envs/cyber-cuda/lib/python3.11/site-packages/nvidia/*/lib; do
  [[ -d "$libdir" ]] && cuda_lib_path="${cuda_lib_path:+$cuda_lib_path:}$libdir"
done
export LD_LIBRARY_PATH="${cuda_lib_path}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
readonly SERVER="$RUNTIME/llama-server"
readonly GPT_MODEL="$MODEL_DIR/gpt-oss-20b-UD-Q4_K_XL.gguf"
readonly GEMMA_MODEL="$MODEL_DIR/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"
test -x "$SERVER" && test -s "$GPT_MODEL" && test -s "$GEMMA_MODEL"

gpt_pid=""; gemma_pid=""; forward_pid=""
cleanup() {
  [[ -n "$forward_pid" ]] && kill "$forward_pid" 2>/dev/null || true
  [[ -n "$gemma_pid" ]] && kill "$gemma_pid" 2>/dev/null || true
  [[ -n "$gpt_pid" ]] && kill "$gpt_pid" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM
echo "started_at=$(date -Is) host=$(hostname) job=$SLURM_JOB_ID compute=cpu-only"

common_args=(--host 127.0.0.1 --ctx-size 4096 --parallel 1 --n-gpu-layers 0
  --threads 12 --threads-batch 12 --reasoning auto --reasoning-format auto
  --temp 0.12 --top-p 0.9 --top-k 0 --min-p 0 --dry-multiplier 0
  --repeat-penalty 1.12 --repeat-last-n 128 --no-webui)
"$SERVER" --model "$GPT_MODEL" --port 18081 "${common_args[@]}" \
  >"$LOG_DIR/phase107-gptoss-cpu-$SLURM_JOB_ID.log" 2>&1 &
gpt_pid=$!

wait_health() {
  local url="$1" pid="$2" label="$3" deadline=$((SECONDS + 900))
  until curl -fsS --max-time 3 "$url" >/dev/null; do
    kill -0 "$pid" 2>/dev/null || { echo "$label server exited before health" >&2; return 1; }
    (( SECONDS < deadline )) || { echo "$label server health timeout" >&2; return 1; }
    sleep 5
  done
  echo "$label health=ok"
}
wait_health http://127.0.0.1:18081/health "$gpt_pid" gptoss
"$SERVER" --model "$GEMMA_MODEL" --port 18082 "${common_args[@]}" \
  >"$LOG_DIR/phase107-gemma4-cpu-$SLURM_JOB_ID.log" 2>&1 &
gemma_pid=$!
wait_health http://127.0.0.1:18082/health "$gemma_pid" gemma4

# Reverse SSH ports bind to login-node loopback only; no campus/public listener.
ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -N \
  -R 127.0.0.1:39081:127.0.0.1:18081 \
  -R 127.0.0.1:39082:127.0.0.1:18082 \
  zj225@slurmc.ie.cuhk.edu.hk >"$LOG_DIR/phase107-cpu-reverse-tunnel-$SLURM_JOB_ID.log" 2>&1 &
forward_pid=$!
sleep 2
kill -0 "$forward_pid" || { echo "reverse SSH tunnel failed" >&2; exit 5; }
echo "reference_servers_ready=true compute=cpu-only threads_per_server=12; requests are sequential"
while kill -0 "$gpt_pid" 2>/dev/null && kill -0 "$gemma_pid" 2>/dev/null && kill -0 "$forward_pid" 2>/dev/null; do sleep 30; done
echo "reference server or tunnel exited unexpectedly" >&2
exit 6
