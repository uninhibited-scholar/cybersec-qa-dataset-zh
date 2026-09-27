#!/bin/bash
# CPU-only integrity check, scheduled after the blinded collector terminates.
# It does not perform inference, scoring, or identity-map unblinding.
# The compute node cannot reach slurmdbd; supply a freshly queried login-node
# sacct snapshot via COLLECTION_STATE, COLLECTION_EXIT_CODE, and
# COLLECTION_STATUS_OBSERVED_AT when submitting with afterany:44803.
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
PYTHON="$HOME/miniforge3/envs/coevo/bin/python"
RUN_DIR="$ROOT/results/phase108-v18r2-blind-44803"
CASES="$ROOT/data/phase108-eval-private-v18r2/phase108-private-cases-v1.8-rev2.json"
FREEZE="$ROOT/data/phase108-eval-private-v18r2/freeze-v1.8-rev2.json"
VERIFIER="$ROOT/data/training/phase108_verify_blind_collection_v18r2.py"
RESULT="$RUN_DIR/integrity-report.json"
RESULT_TMP="$RUN_DIR/integrity-report.json.tmp.$SLURM_JOB_ID"
COLLECTION_STATE="${COLLECTION_STATE:?submit with a fresh login-node sacct snapshot}"
COLLECTION_EXIT_CODE="${COLLECTION_EXIT_CODE:?submit with a fresh login-node sacct snapshot}"
COLLECTION_STATUS_OBSERVED_AT="${COLLECTION_STATUS_OBSERVED_AT:?submit with a fresh login-node sacct snapshot}"

test -x "$PYTHON"
test -d "$RUN_DIR"
test ! -e "$RESULT"
test ! -e "$RESULT_TMP"
cd "$ROOT/data/training"

# Purely synthetic unit tests; no private evaluation artifacts are opened here.
"$PYTHON" -m unittest test_phase108_verify_blind_collection_v18r2 -v

# The verifier first checks authoritative sacct state and refuses incomplete
# jobs. It validates all three aliases but deliberately leaves them blinded.
"$PYTHON" "$VERIFIER" \
  --run-dir "$RUN_DIR" \
  --cases "$CASES" \
  --freeze "$FREEZE" \
  --job-id 44803 \
  --slurm-state "$COLLECTION_STATE" \
  --slurm-exit-code "$COLLECTION_EXIT_CODE" \
  --slurm-observed-at "$COLLECTION_STATUS_OBSERVED_AT" > "$RESULT_TMP"
chmod 600 "$RESULT_TMP"
mv "$RESULT_TMP" "$RESULT"
echo "BLIND_COLLECTION_INTEGRITY=PASS report=$RESULT"
