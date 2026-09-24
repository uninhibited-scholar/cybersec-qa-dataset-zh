#!/bin/bash
# A100 compatibility smoke test for community GPTQ INT8 weights.
# Does not touch production API.
#SBATCH --job-name=qwen32b-int8-smoke
#SBATCH --partition=GPU-LARGE
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/qwen32b-int8-gpu-smoke-%j.log
set -euo pipefail
ROOT=/data3/ieug25/zj225/cyber-model-migration
PY=/data3/ieug25/zj225/venvs/qwen-int8/bin/python
MODEL=/data3/ieug25/zj225/models/Qwen3-32B-GPTQ-Int8
test -f "$MODEL/model.safetensors.index.json"
exec "$PY" "$ROOT/data/training/qwen32b_smoke.py" --model "$MODEL" --device cuda
