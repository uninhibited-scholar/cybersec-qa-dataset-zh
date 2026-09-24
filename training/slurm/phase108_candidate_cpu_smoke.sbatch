#!/bin/bash
# CPU-only fallback: public compatibility probe, not a benchmark.
#SBATCH --job-name=phase108-cpu-smoke
#SBATCH --partition=GPU-MEDIUM
#SBATCH --cpus-per-task=12
#SBATCH --mem=48G
#SBATCH --time=01:30:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-cpu-smoke-%j.log

set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
ADAPTER="$ROOT/models/phase108-cuda-recovery-12000-20260921-gpumed-r3/0007000_adapters.safetensors"
EXPECTED_ADAPTER_SHA256=919a9eabe4a9c2fab1c66a99d3e9265fab196c34852c2489076c6b2e6b29a2d3
RUNNER="$ROOT/data/training/phase108_cpu_diagnostic.py"
OUTPUT="$ROOT/results/phase108-candidate-cpu-smoke-0007000.jsonl"

test -r "$BASE/config.json"
test -r "$ADAPTER"
test -r "$RUNNER"
test ! -e "$OUTPUT"
test "$(sha256sum "$ADAPTER" | awk '{print $1}')" = "$EXPECTED_ADAPTER_SHA256"
"$PYTHON" "$RUNNER" --base "$BASE" --adapter "$ADAPTER" \
  --expected-adapter-sha256 "$EXPECTED_ADAPTER_SHA256" --output "$OUTPUT" --max-new-tokens 32
test "$(wc -l < "$OUTPUT" | tr -d ' ')" = 4
echo "cpu_public_smoke_complete=true"
