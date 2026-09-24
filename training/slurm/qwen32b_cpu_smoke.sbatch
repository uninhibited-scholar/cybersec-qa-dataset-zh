#!/bin/bash
#SBATCH --job-name=qwen32b-cpu-smoke
#SBATCH --partition=GPU-LARGE
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/qwen32b-cpu-smoke-%j.log
set -euo pipefail
ROOT=/data3/ieug25/zj225/cyber-model-migration
PY=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
MODEL=/data3/ieug25/zj225/models/Qwen3-32B-FP8
test -f "$MODEL/model.safetensors.index.json"
exec "$PY" "$ROOT/data/training/qwen32b_smoke.py" --model "$MODEL" --device cpu
