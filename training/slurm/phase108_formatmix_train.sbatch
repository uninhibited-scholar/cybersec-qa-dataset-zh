#!/bin/bash
# Isolated follow-up candidate: mixed prompt formats; production untouched.
#SBATCH --job-name=phase108-formatmix
#SBATCH --partition=GPU-LARGE
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=2-00:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-formatmix-%j.log
set -euo pipefail
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
INPUT="$ROOT/models/phase108-step12000-20260920/0012000_adapters.safetensors"
DATA="$ROOT/data/phase108-clean-v3-formatmix"
OUTPUT="$ROOT/models/phase108-formatmix-20260925"
EXPECTED=3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036
test -r "$BASE/config.json" -a -r "$INPUT" -a -r "$DATA/train.jsonl" -a -r "$DATA/valid.jsonl"
test ! -e "$OUTPUT"
test "$(sha256sum "$INPUT" | awk '{print $1}')" = "$EXPECTED"
"$PYTHON" "$ROOT/data/training/scripts/phase108_cuda_resume_train.py" \
  --base "$BASE" --adapter "$INPUT" --data "$DATA" --output "$OUTPUT" \
  --max-steps 7621 --batch-size 1 --grad-accumulation 2 --learning-rate 5e-6 \
  --max-length 2304 --save-every 1000 --seed 20260925
