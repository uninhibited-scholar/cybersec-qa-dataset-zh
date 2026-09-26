#!/bin/bash
# Frozen raw-weight comparison on the reviewed Phase108 v1.8-rev2 holdout.
# This collects blinded outputs only; it does not score or promote a model.
#SBATCH --job-name=p108-v18r2-blind
#SBATCH --partition=GPU-TITANX
#SBATCH --gres=gpu:TITANX:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=1-00:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-v18r2-blind-%j.log
#SBATCH --error=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-v18r2-blind-%j.err

set -euo pipefail
umask 077
on_err() { status=$?; echo "wrapper_error status=$status line=$LINENO"; exit "$status"; }
trap on_err ERR
echo "wrapper_started job_id=${SLURM_JOB_ID:-unknown} node=${SLURM_NODELIST:-unknown}"

ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
PARENT="$ROOT/models/phase108-step12000-20260920/0012000_adapters.safetensors"
CANDIDATE="$ROOT/models/phase108-cuda-recovery-scale20-corrected-20260924-r2/adapters.safetensors"
CASES="$ROOT/data/phase108-eval-private-v18r2/phase108-private-cases-v1.8-rev2.json"
FREEZE="$ROOT/data/phase108-eval-private-v18r2/freeze-v1.8-rev2.json"
SCRIPT="$ROOT/data/training/phase108_blind_collection_v18r2.py"
LOADER="$ROOT/data/training/phase108_hf_adapter_smoke.py"
TESTS="$ROOT/data/training/test_phase108_blind_collection_v18r2.py"
RUN_DIR="$ROOT/results/phase108-v18r2-blind-$SLURM_JOB_ID"

EXPECTED_CASES_SHA=c028b564d2273fc6779f248918511fa2bff0fe73abc4c7bb4ab6051ecc3b91c9
EXPECTED_FREEZE_SHA=1dd603084fe3f026954ead8cb55004514b1c5b43a3b3219b0b10b0489ac0d5bf
EXPECTED_PARENT_SHA=3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036
EXPECTED_CANDIDATE_SHA=4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772
EXPECTED_COLLECTOR_SHA=8ce85906bd41c097ca9c8a2296bdb73f43ee2a468640a54be1506a66c5788c6e
EXPECTED_LOADER_SHA=00ef5d3b1aaada8285b711a68f47c9e00a4fb9dbbd993e8eaf8eefd7426fa371
EXPECTED_TEST_SHA=f3003eaf0d64e0d7a33f4b57407af150acfa839e0c00eaba79598a22924d7161

check_hash() {
  local path="$1" expected="$2" actual
  if [[ ! -r "$path" ]]; then
    echo "preflight_missing_file=$path" >&2
    return 1
  fi
  actual=$(sha256sum "$path" | awk '{print $1}') || {
    echo "preflight_hash_command_failed=$path" >&2
    return 1
  }
  if [[ "$actual" != "$expected" ]]; then
    echo "preflight_hash_mismatch=$path expected=$expected actual=$actual" >&2
    return 1
  fi
  echo "preflight_hash_verified=${path##*/}"
}

check_hash "$CASES" "$EXPECTED_CASES_SHA"
check_hash "$FREEZE" "$EXPECTED_FREEZE_SHA"
check_hash "$PARENT" "$EXPECTED_PARENT_SHA"
check_hash "$CANDIDATE" "$EXPECTED_CANDIDATE_SHA"
check_hash "$SCRIPT" "$EXPECTED_COLLECTOR_SHA"
check_hash "$LOADER" "$EXPECTED_LOADER_SHA"
check_hash "$TESTS" "$EXPECTED_TEST_SHA"
for required in "$BASE/config.json" "$BASE/model.safetensors.index.json" "$SCRIPT" "$LOADER"; do
  if [[ ! -r "$required" ]]; then
    echo "preflight_missing_file=$required" >&2
    exit 1
  fi
done
if [[ -e "$RUN_DIR" ]]; then
  echo "preflight_output_path_exists=$RUN_DIR" >&2
  exit 1
fi
mkdir -m 700 "$RUN_DIR" || { echo "preflight_mkdir_failed=$RUN_DIR" >&2; exit 1; }
echo "hash_preflight_complete run_dir=$RUN_DIR"

export PYTHONPATH="$ROOT/data/training${PYTHONPATH:+:$PYTHONPATH}"
cd "$ROOT/data/training"
"$PYTHON" -m unittest test_phase108_blind_collection_v18r2 -v
cd "$ROOT"
echo "unit_tests_complete; starting isolated inference"
"$PYTHON" -u "$SCRIPT" \
  --base "$BASE" \
  --parent-adapter "$PARENT" \
  --candidate-adapter "$CANDIDATE" \
  --cases "$CASES" \
  --freeze "$FREEZE" \
  --job-script "$0" \
  --adapter-loader "$LOADER" \
  --output-dir "$RUN_DIR"

echo "blind_collection_complete=true scored=false promotion_eligible=false production_changed=false run_dir=$RUN_DIR"
