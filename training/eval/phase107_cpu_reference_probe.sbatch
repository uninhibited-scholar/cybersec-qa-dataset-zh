#!/usr/bin/env bash
# CPU-only feasibility probe for the pinned Phase 107 GPT-OSS GGUF reference.
# This is an infrastructure smoke test, not a benchmark prompt or score.
#SBATCH --job-name=phase107-cpu-probe
#SBATCH --partition=GPU-LARGE
#SBATCH --nodelist=a100-3
#SBATCH --cpus-per-task=12
#SBATCH --mem=48G
#SBATCH --time=00:15:00
#SBATCH --output=phase107-cpu-probe-%j.out

set -euo pipefail

readonly ROOT="$HOME/cyber-model-migration/phase107-runtime"
readonly RUNTIME="$ROOT/llama-b11046-cuda-12.8-x64/llama-b11046"
readonly MODEL_NAME="${PHASE107_CPU_PROBE_MODEL:-gpt-oss-20b-UD-Q4_K_XL.gguf}"
case "$MODEL_NAME" in
  gpt-oss-20b-UD-Q4_K_XL.gguf|gemma-4-26B-A4B-it-UD-Q4_K_M.gguf) ;;
  *) echo "unapproved probe model filename" >&2; exit 1 ;;
esac
readonly MODEL="$ROOT/models/$MODEL_NAME"
readonly LOG_DIR="$ROOT/logs"
readonly PORT=18083
mkdir -p "$LOG_DIR"
test -x "$RUNTIME/llama-server" && test -s "$MODEL"

cuda_lib_path=""
for libdir in "$HOME"/miniforge3/envs/cyber-cuda/lib/python3.11/site-packages/nvidia/*/lib; do
  [[ -d "$libdir" ]] && cuda_lib_path="${cuda_lib_path:+$cuda_lib_path:}$libdir"
done
export LD_LIBRARY_PATH="${cuda_lib_path}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

server_log="$LOG_DIR/phase107-cpu-probe-server-$SLURM_JOB_ID.log"
summary="$LOG_DIR/phase107-cpu-probe-summary-$SLURM_JOB_ID.json"
server_pid=""
cleanup() {
  [[ -n "$server_pid" ]] && kill "$server_pid" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

started=$(date +%s)
"$RUNTIME/llama-server" --model "$MODEL" --host 127.0.0.1 --port "$PORT" \
  --ctx-size 4096 --parallel 1 --n-gpu-layers 0 --threads 12 \
  --reasoning auto --reasoning-format auto \
  --temp 0.12 --top-p 0.9 --top-k 0 --min-p 0 --dry-multiplier 0 \
  --repeat-penalty 1.12 --repeat-last-n 128 --no-webui \
  >"$server_log" 2>&1 &
server_pid=$!

deadline=$((SECONDS + 600))
until curl -fsS --max-time 2 "http://127.0.0.1:$PORT/health" >/dev/null; do
  kill -0 "$server_pid" 2>/dev/null || { echo "server exited before health" >&2; exit 2; }
  (( SECONDS < deadline )) || { echo "CPU reference health timeout" >&2; exit 3; }
  sleep 2
done
loaded=$(date +%s)

http_code=$(curl -sS --max-time 240 -o "$LOG_DIR/phase107-cpu-probe-response-$SLURM_JOB_ID.json" \
  -w '%{http_code}' "http://127.0.0.1:$PORT/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Say exactly READY."}],"max_tokens":700,"temperature":0.12,"top_p":0.9,"repeat_penalty":1.12,"repeat_last_n":128,"stream":false}')
completed=$(date +%s)

python3 - "$summary" "$http_code" "$started" "$loaded" "$completed" "$LOG_DIR/phase107-cpu-probe-response-$SLURM_JOB_ID.json" "$MODEL_NAME" <<'PY'
import json, pathlib, sys
summary_path, status, started, loaded, completed, response_path, model_name = sys.argv[1:]
response = json.loads(pathlib.Path(response_path).read_text())
choice = (response.get("choices") or [{}])[0]
usage = response.get("usage") or {}
result = {
    "http_status": int(status),
    "health_and_model_load_seconds": int(loaded) - int(started),
    "request_total_seconds": int(completed) - int(loaded),
    "completion_tokens": usage.get("completion_tokens"),
    "finish_reason": choice.get("finish_reason"),
    "nonempty_content": bool((choice.get("message") or {}).get("content", "").strip()),
    "hardware_mode": "CPU-only (n_gpu_layers=0)",
    "model_file": model_name,
}
pathlib.Path(summary_path).write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
if int(status) != 200 or not result["nonempty_content"]:
    raise SystemExit(4)
PY
