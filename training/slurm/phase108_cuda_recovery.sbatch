#!/bin/bash
# Isolated Phase108 recovery candidate. It must never be pointed at production.
# Submit from /data3/ieug25/zj225/cyber-model-migration after syncing the script.
#SBATCH --job-name=phase108cuda
# 2,304-token BF16 training exceeds the ~10.6 GiB RTX2080 allocation.
# GPU-MEDIUM exposes the available 20/24 GiB class devices.
#SBATCH --partition=GPU-MEDIUM
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=20:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-cuda-%j.log

set -euo pipefail
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
export TOKENIZERS_PARALLELISM=false
"$PYTHON" "$ROOT/data/training/scripts/phase108_cuda_resume_train.py" \
  --base "$ROOT/models/base-phase3-dequantized" \
  --adapter "$ROOT/models/phase108-step12000-20260920/0012000_adapters.safetensors" \
  --data "$ROOT/data/phase108-clean-v2" \
  --output "$ROOT/models/phase108-cuda-recovery-12000-20260921-gpumed-r3" \
  --max-steps 7621 --batch-size 1 --grad-accumulation 2 --learning-rate 5e-6 \
  --max-length 2304 --save-every 1000 --seed 20260920
