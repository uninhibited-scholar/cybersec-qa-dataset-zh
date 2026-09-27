#!/bin/bash
# CPU-only, post-integrity blind-review bundle preparation.
# Submit only after the integrity verifier succeeds, with
# --export=ALL,INTEGRITY_JOB_ID=<id> --dependency=afterok:<id>.
# No GPU, model inference, scoring, identity-map read, or label reveal occurs.
#SBATCH --job-name=p108-review-pack
#SBATCH --partition=GPU-TITANX
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:20:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-v18r2-pack-%j.log
#SBATCH --error=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-v18r2-pack-%j.err

set -euo pipefail
umask 077

ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON="$HOME/miniforge3/envs/coevo/bin/python"
RUN_DIR="$ROOT/results/phase108-v18r2-blind-44803"
CASES="$ROOT/data/phase108-eval-private-v18r2/phase108-private-cases-v1.8-rev2.json"
FREEZE="$ROOT/data/phase108-eval-private-v18r2/freeze-v1.8-rev2.json"
KEYS="$ROOT/data/phase108-eval-private-v18r2/phase108-answer-keys-v1.8-rev2.json"
PACKER_DIR="$ROOT/data/training/phase108-review-pack-v18r2"
PACKER="$PACKER_DIR/phase108_prepare_blind_review_v18r2.py"
OUTDIR="/data3/ieug25/zj225/phase108-v18r2-blind-review-44803"
INTEGRITY_JOB_ID="${INTEGRITY_JOB_ID:?submit with INTEGRITY_JOB_ID set to the successful verifier job}"

test -x "$PYTHON"
test -d "$RUN_DIR"
test -f "$RUN_DIR/integrity-report.json"
test -f "$KEYS"
test ! -e "$OUTDIR"
test "$(stat -c '%a' "$RUN_DIR")" = 700
test "$(stat -c '%a' "$RUN_DIR/integrity-report.json")" = 600
test "$(stat -c '%a' "$KEYS")" = 600
test "$(stat -c '%a' "$PACKER_DIR")" = 700

cd "$PACKER_DIR"
"$PYTHON" -m unittest -v test_phase108_prepare_blind_review_v18r2

"$PYTHON" "$PACKER" \
  --run-dir "$RUN_DIR" \
  --cases "$CASES" \
  --freeze "$FREEZE" \
  --keys "$KEYS" \
  --rubric "$PACKER_DIR/phase107-rubric-v0.1.md" \
  --protocol "$PACKER_DIR/phase107-inference-protocol-v0.1.md" \
  --corrigendum "$PACKER_DIR/phase107-inference-protocol-v0.1-corrigendum-v0.1.1.md" \
  --outdir "$OUTDIR" \
  --repo-root "$ROOT" \
  --job-id 44803 \
  --integrity-job-id "$INTEGRITY_JOB_ID"

echo "BLIND_REVIEW_BUNDLE_READY output=$OUTDIR"
