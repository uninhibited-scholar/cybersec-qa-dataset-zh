#!/bin/bash
# Isolated fixed validation for the scale-corrected Phase108 candidate.
# No deployment, API, training, rubric, or test-split access.
# Submit with immutable numbered checkpoint and observed SHA.
# shellcheck disable=SC1091
#SBATCH --job-name=phase108-r2-val
#SBATCH --partition=GPU-MEDIUM
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-r2-validation-%j.log

set -euo pipefail
ROOT=/data3/ieug25/zj225/cyber-model-migration
BASE="$ROOT/models/base-phase3-dequantized"
VALIDATION="$ROOT/data/phase108-clean-v2/valid.jsonl"
VALIDATION_SHA256=44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365
RUNNER="$ROOT/data/training/scripts/phase108_cuda_full_validation.py"
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
PHASE108_ADAPTER=${PHASE108_ADAPTER:?pass an immutable numbered corrected-r2 checkpoint}
PHASE108_ADAPTER_SHA256=${PHASE108_ADAPTER_SHA256:?pass observed checkpoint SHA-256}

case "$PHASE108_ADAPTER" in
  "$ROOT"/models/phase108-cuda-recovery-scale20-corrected-20260924-r2/[0-9][0-9][0-9][0-9][0-9][0-9][0-9]_adapters.safetensors) ;;
  *) echo "refusing non-numbered corrected-r2 adapter" >&2; exit 64 ;;
esac
test -r "$BASE/config.json" -a -r "$VALIDATION" -a -r "$RUNNER" -a -r "$PHASE108_ADAPTER"
test "$(sha256sum "$VALIDATION" | awk '{print $1}')" = "$VALIDATION_SHA256"
test "$(sha256sum "$PHASE108_ADAPTER" | awk '{print $1}')" = "$PHASE108_ADAPTER_SHA256"
"$PYTHON" "$RUNNER" --base "$BASE" --adapter "$PHASE108_ADAPTER" \
  --validation "$VALIDATION" --expected-validation-sha256 "$VALIDATION_SHA256" \
  --expected-adapter-sha256 "$PHASE108_ADAPTER_SHA256" --max-length 2304
