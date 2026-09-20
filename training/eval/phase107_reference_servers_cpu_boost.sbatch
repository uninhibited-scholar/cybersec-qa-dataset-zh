#!/usr/bin/env bash
# CPU-only, resumable Phase 107 reference collection on spare a100-2 CPU cores.
# Protocol/model files stay frozen; only CPU allocation/host changes.
#SBATCH --job-name=phase107-cpu-boost
#SBATCH --partition=GPU-MEDIUM
#SBATCH --nodelist=a100-2
#SBATCH --cpus-per-task=24
#SBATCH --mem=48G
#SBATCH --time=2-00:00:00
#SBATCH --output=logs/phase107-cpu-boost-%j.out

set -euo pipefail
readonly ROOT="$HOME/cyber-model-migration/phase107-runtime"
readonly RUNTIME="$ROOT/llama-b11046-cuda-12.8-x64/llama-b11046"
readonly MODEL_DIR="$ROOT/models"
readonly LOG_DIR="$ROOT/logs"
readonly THREADS="${SLURM_CPUS_PER_TASK:?Slurm CPU allocation is required}"
(( THREADS % 2 == 0 )) || { echo "CPU allocation must split evenly between reference servers" >&2; exit 8; }
readonly SERVER_THREADS="$((THREADS / 2))"
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

python3 - <<'PY'
import socket
for port in (18081, 18082):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", port))
PY

gpt_pid=""; gemma_pid=""
cleanup() {
  [[ -n "$gemma_pid" ]] && kill "$gemma_pid" 2>/dev/null || true
  [[ -n "$gpt_pid" ]] && kill "$gpt_pid" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM
echo "started_at=$(date -Is) host=$(hostname) job=$SLURM_JOB_ID total_threads=$THREADS server_threads=$SERVER_THREADS compute=cpu-only"

common_args=(--host 127.0.0.1 --ctx-size 4096 --parallel 1 --n-gpu-layers 0
  --threads "$SERVER_THREADS" --threads-batch "$SERVER_THREADS" --reasoning auto --reasoning-format auto
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
  kill -0 "$pid" 2>/dev/null || { echo "$label server exited after health" >&2; return 1; }
  echo "$label health=ok pid=$pid"
}
wait_health http://127.0.0.1:18081/health "$gpt_pid" gptoss
"$SERVER" --model "$GEMMA_MODEL" --port 18082 "${common_args[@]}" \
  >"$LOG_DIR/phase107-gemma4-cpu-$SLURM_JOB_ID.log" 2>&1 &
gemma_pid=$!
wait_health http://127.0.0.1:18082/health "$gemma_pid" gemma4

echo "reference_servers_ready=true compute=cpu-only threads_per_server=$SERVER_THREADS; reference calls will overlap with randomized start order"
if [[ -n "${PHASE107_REFERENCE_COLLECTION_DIR:-}" ]]; then
  readonly COLLECTION_DIR="$PHASE107_REFERENCE_COLLECTION_DIR"
  case "$COLLECTION_DIR" in
    "$ROOT"/phase107-cpu-collection-*) ;;
    *) echo "refusing collection directory outside the private Phase 107 staging prefix" >&2; exit 7 ;;
  esac
  test -s "$COLLECTION_DIR/phase107_collect_blind.py"
  test -s "$COLLECTION_DIR/phase107-private-cases-v0.2.json"
  echo "starting_reference_collection=$COLLECTION_DIR"
  PHASE107_REFERENCE_EXECUTION_MODE="cpu-only a100-2; llama.cpp b11046; n_gpu_layers=0; $SERVER_THREADS threads per server; randomized reference calls overlap" \
    python3 -u "$COLLECTION_DIR/phase107_collect_blind.py" \
      --cases "$COLLECTION_DIR/phase107-private-cases-v0.2.json" \
      --outdir "$COLLECTION_DIR" --systems phase91 gptoss20b gemma4_26b \
      --reference-host "$(hostname)" --reference-local --parallel-reference-arms
  echo "reference_collection_completed=true"
fi
while kill -0 "$gpt_pid" 2>/dev/null && kill -0 "$gemma_pid" 2>/dev/null; do sleep 30; done
echo "reference server exited unexpectedly" >&2
exit 6
