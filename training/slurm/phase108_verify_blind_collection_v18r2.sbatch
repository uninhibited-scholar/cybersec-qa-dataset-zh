#!/bin/bash
# CPU-only integrity check, scheduled after the blinded collector terminates.
# It does not perform inference, scoring, or identity-map unblinding.
# Submit with: sbatch --dependency=afterany:44803 this-file
#SBATCH --job-name=p108-blind-verify
#SBATCH --partition=GPU-TITANX
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:10:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-v18r2-verify-%j.log
#SBATCH --error=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-v18r2-verify-%j.err

set -euo pipefail
umask 077

ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON="$ROOT/miniforge3/envs/coevo/bin/python"
RUN_DIR="$ROOT/results/phase108-v18r2-blind-44803"
CASES="$ROOT/data/phase108-eval-private-v18r2/phase108-private-cases-v1.8-rev2.json"
FREEZE="$ROOT/data/phase108-eval-private-v18r2/freeze-v1.8-rev2.json"
VERIFIER="$ROOT/data/training/phase108_verify_blind_collection_v18r2.py"
RESULT="$RUN_DIR/integrity-report.json"

test -x "$PYTHON"
test -d "$RUN_DIR"
test ! -e "$RESULT"
cd "$ROOT/data/training"

# Purely synthetic unit tests; no private evaluation artifacts are opened here.
"$PYTHON" -m unittest test_phase108_verify_blind_collection_v18r2 -v

# The verifier first checks authoritative sacct state and refuses incomplete
# jobs. It validates all three aliases but deliberately leaves them blinded.
"$PYTHON" "$VERIFIER" \
  --run-dir "$RUN_DIR" \
  --cases "$CASES" \
  --freeze "$FREEZE" \
  --job-id 44803 > "$RESULT"
chmod 600 "$RESULT"
echo "BLIND_COLLECTION_INTEGRITY=PASS report=$RESULT"
