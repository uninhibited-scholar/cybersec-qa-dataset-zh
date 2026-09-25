#!/bin/bash
# Public development diagnostics only; not a blind benchmark or promotion gate.
# Sequentially compare the exact Phase108 parent and corrected-r2 final adapter
# with the same four benign probes. Raw outputs remain private outside Git.
#SBATCH --job-name=p108-parent-cand-diag
#SBATCH --partition=GPU-MEDIUM
#SBATCH --gres=gpu:RTX-3090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:45:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-pair-diag-%j.log

set -euo pipefail
umask 077
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
PARENT="$ROOT/models/phase108-step12000-20260920/0012000_adapters.safetensors"
CANDIDATE="$ROOT/models/phase108-cuda-recovery-scale20-corrected-20260924-r2/adapters.safetensors"
DIAG="$ROOT/data/training/phase108_cuda_diagnostic.py"
ADAPTER_HELPER="$ROOT/data/training/phase108_hf_adapter_smoke.py"
RUN_DIR="$ROOT/results/phase108-public-diagnostic-$SLURM_JOB_ID"

readonly PARENT_SHA256=3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036
readonly CANDIDATE_SHA256=4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772
readonly DIAG_SHA256=c5a42485f688998ed3f539f1ff751e96d5c685e26d7bf16f25a23ef3f8f621e2
readonly ADAPTER_HELPER_SHA256=00ef5d3b1aaada8285b711a68f47c9e00a4fb9dbbd993e8eaf8eefd7426fa371

for path in "$BASE/config.json" "$PARENT" "$CANDIDATE" "$DIAG" "$ADAPTER_HELPER"; do test -r "$path"; done
test "$(sha256sum "$PARENT" | awk '{print $1}')" = "$PARENT_SHA256"
test "$(sha256sum "$CANDIDATE" | awk '{print $1}')" = "$CANDIDATE_SHA256"
test "$(sha256sum "$DIAG" | awk '{print $1}')" = "$DIAG_SHA256"
test "$(sha256sum "$ADAPTER_HELPER" | awk '{print $1}')" = "$ADAPTER_HELPER_SHA256"
test ! -e "$RUN_DIR"
mkdir -m 700 "$RUN_DIR"

echo "PUBLIC_DIAGNOSTIC_ONLY=true blind=false rubric_score=false production=false tools=[]"
echo "parent_sha256=$PARENT_SHA256 candidate_sha256=$CANDIDATE_SHA256"
"$PYTHON" -u "$DIAG" --base "$BASE" --adapter "$PARENT" \
  --output "$RUN_DIR/parent.jsonl" --dtype bfloat16 --max-new-tokens 96
"$PYTHON" -u "$DIAG" --base "$BASE" --adapter "$CANDIDATE" \
  --output "$RUN_DIR/candidate.jsonl" --dtype bfloat16 --max-new-tokens 96
chmod 600 "$RUN_DIR"/*.jsonl
sha256sum "$RUN_DIR"/*.jsonl >"$RUN_DIR/output-sha256.txt"
chmod 600 "$RUN_DIR/output-sha256.txt"
echo "PUBLIC_DIAGNOSTIC_COMPLETE=true output_dir=$RUN_DIR"
