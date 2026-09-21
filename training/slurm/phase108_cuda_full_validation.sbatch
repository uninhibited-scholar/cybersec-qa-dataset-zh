#!/bin/bash
# Selection-only evaluator.  Submit only after the isolated trainer has exited:
#   sbatch --export=ALL,PHASE108_ADAPTER=/absolute/0004000_adapters.safetensors,PHASE108_ADAPTER_SHA256=<sha256> phase108_cuda_full_validation.sbatch
# This job has no deployment, API, training, test-split, or checkpoint-writing path.
#SBATCH --job-name=phase108-full-val
#SBATCH --partition=GPU-MEDIUM
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-full-validation-%j.log

set -euo pipefail

: "${PHASE108_ADAPTER:?pass an immutable numbered candidate checkpoint}"
: "${PHASE108_ADAPTER_SHA256:?pass the checkpoint SHA-256 observed before submission}"

ROOT=/data3/ieug25/zj225/cyber-model-migration
BASE="$ROOT/models/base-phase3-dequantized"
VALIDATION="$ROOT/data/phase108-clean-v2/valid.jsonl"
VALIDATION_SHA256=44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365
RUNNER="$ROOT/data/training/scripts/phase108_cuda_full_validation.py"
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python

case "$PHASE108_ADAPTER" in
  "$ROOT"/models/phase108-cuda-recovery-12000-20260921-gpumed-r3/[0-9][0-9][0-9][0-9][0-9][0-9][0-9]_adapters.safetensors) ;;
  *) echo "refusing non-numbered or non-Phase108 candidate adapter" >&2; exit 64 ;;
esac

test -r "$PHASE108_ADAPTER"
test -r "$VALIDATION"
test -r "$RUNNER"
"$PYTHON" "$RUNNER" \
  --base "$BASE" \
  --adapter "$PHASE108_ADAPTER" \
  --validation "$VALIDATION" \
  --expected-validation-sha256 "$VALIDATION_SHA256" \
  --expected-adapter-sha256 "$PHASE108_ADAPTER_SHA256" \
  --max-length 2304
