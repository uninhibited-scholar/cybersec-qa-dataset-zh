#!/bin/bash
# Isolated Phase108 scale-corrected candidate.  It starts from the immutable
# MLX Phase108 checkpoint but never changes production or an existing candidate.
# PEFT uses alpha=160 so alpha/rank equals MLX's direct scale=20.
#SBATCH --job-name=phase108-scale20
#SBATCH --partition=GPU-LARGE
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=20:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-scale20-%j.log

set -euo pipefail
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
INPUT_ADAPTER="$ROOT/models/phase108-step12000-20260920/0012000_adapters.safetensors"
DATA="$ROOT/data/phase108-clean-v2"
OUTPUT="$ROOT/models/phase108-cuda-recovery-scale20-corrected-20260924-r2"
EXPECTED_INPUT_SHA256=3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036

test -r "$BASE/config.json"
test -r "$INPUT_ADAPTER"
test -r "$DATA/train.jsonl"
test -r "$DATA/valid.jsonl"
test ! -e "$OUTPUT"
test "$(sha256sum "$INPUT_ADAPTER" | awk '{print $1}')" = "$EXPECTED_INPUT_SHA256"
# Refuse to train if the invoked remote runner is the stale alpha=20 version.
RUNNER="$ROOT/data/training/scripts/phase108_cuda_resume_train.py"
test -r "$RUNNER"
grep -q 'peft_lora_alpha = mlx_scale_to_peft_alpha' "$RUNNER"
grep -q '"peft_effective_scale"' "$RUNNER"
export TOKENIZERS_PARALLELISM=false
export PYTHONDONTWRITEBYTECODE=1
"$PYTHON" "$RUNNER" \
  --base "$BASE" --adapter "$INPUT_ADAPTER" --data "$DATA" --output "$OUTPUT" \
  --max-steps 7621 --batch-size 1 --grad-accumulation 2 --learning-rate 5e-6 \
  --max-length 2304 --save-every 1000 --seed 20260920
