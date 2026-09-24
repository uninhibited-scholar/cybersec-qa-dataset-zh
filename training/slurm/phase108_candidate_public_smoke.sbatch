#!/bin/bash
# Read-only compatibility smoke for the selected Phase108 candidate.
# This is deliberately not a blind benchmark, a deployment task, or a claim
# about cybersecurity capability.  It runs four public development probes and
# writes one immutable JSONL result on the cluster.
#SBATCH --job-name=phase108-public-smoke
#SBATCH --partition=GPU-MEDIUM
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-public-smoke-%j.log

set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
ADAPTER="$ROOT/models/phase108-cuda-recovery-12000-20260921-gpumed-r3/0007000_adapters.safetensors"
EXPECTED_ADAPTER_SHA256=919a9eabe4a9c2fab1c66a99d3e9265fab196c34852c2489076c6b2e6b29a2d3
RUNNER="$ROOT/data/training/phase108_cuda_diagnostic.py"
OUTPUT="$ROOT/results/phase108-candidate-public-smoke-0007000.jsonl"

test -r "$BASE/config.json"
test -r "$ADAPTER"
test -r "$RUNNER"
test ! -e "$OUTPUT"
actual_sha=$(sha256sum "$ADAPTER" | awk '{print $1}')
test "$actual_sha" = "$EXPECTED_ADAPTER_SHA256"

"$PYTHON" "$RUNNER" \
  --base "$BASE" \
  --adapter "$ADAPTER" \
  --output "$OUTPUT" \
  --dtype bfloat16 \
  --max-new-tokens 96

test "$(wc -l < "$OUTPUT" | tr -d ' ')" = 4
echo "public_smoke_complete=true"
