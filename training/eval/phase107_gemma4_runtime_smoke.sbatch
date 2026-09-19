#!/usr/bin/env bash
# Neutral runtime smoke only: one harmless prompt, no benchmark cases or scoring.
#SBATCH --job-name=p107-gemma4-smoke
#SBATCH --partition=GPU-LARGE
#SBATCH --gres=gpu:A100-40G:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=00:10:00
#SBATCH --output=phase107-gemma4-smoke-%j.out

set -euo pipefail

readonly RUNTIME_DIR="$HOME/cyber-model-migration/phase107-runtime/llama-b11046-cuda-12.8-x64/llama-b11046"
readonly MODEL_PATH="$HOME/cyber-model-migration/phase107-runtime/models/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"
readonly CUDA_LIB_ROOT="$HOME/miniforge3/envs/cyber-cuda/lib/python3.11/site-packages/nvidia"

CUDA_LIB_PATH=""
for libdir in "$CUDA_LIB_ROOT"/*/lib; do
  if [[ -d "$libdir" ]]; then
    CUDA_LIB_PATH="${CUDA_LIB_PATH:+$CUDA_LIB_PATH:}$libdir"
  fi
done
export LD_LIBRARY_PATH="${CUDA_LIB_PATH}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

echo "timestamp=$(date -Is)"
echo "host=$(hostname)"
echo "cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv

readonly CLI="$RUNTIME_DIR/llama-cli"
readonly CUDA_PLUGIN="$RUNTIME_DIR/libggml-cuda.so"
test -x "$CLI"
test -f "$MODEL_PATH"

echo "cuda_plugin_dependencies"
ldd "$CUDA_PLUGIN"
if ldd "$CUDA_PLUGIN" | grep -q 'not found'; then
  echo "CUDA plugin has unresolved shared-library dependencies" >&2
  exit 4
fi

echo "llama_cpp_devices"
"$CLI" --list-devices

echo "neutral_generation_start"
"$CLI" \
  --model "$MODEL_PATH" \
  --gpu-layers 999 \
  --ctx-size 2048 \
  --n-predict 64 \
  --temp 0 \
  --seed 107 \
  --reasoning off \
  --single-turn \
  --no-display-prompt \
  --prompt "Say exactly READY." \
  --simple-io
echo "neutral_generation_exit=0"
