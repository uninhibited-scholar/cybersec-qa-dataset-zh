#!/bin/bash
# Selection-only loss sensitivity diagnostic for one immutable Phase108 adapter.
# Reads valid.jsonl only; no training, test, blind, API, or weight-write path.
# Alternative scales are diagnostic and do not authorize inference/deployment.
#SBATCH --job-name=p108-r2-valscale-grid
#SBATCH --partition=GPU-TITANX
#SBATCH --nodelist=titanv1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=28G
#SBATCH --time=02:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-r2-valscale-grid-%j.log

set -euo pipefail
umask 077
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
export PYTHONPATH="$ROOT/data${PYTHONPATH:+:$PYTHONPATH}"
BASE="$ROOT/models/base-phase3-dequantized"
ADAPTER="$ROOT/models/phase108-cuda-recovery-scale20-corrected-20260924-r2/adapters.safetensors"
VALIDATION="$ROOT/data/phase108-clean-v2/valid.jsonl"
RUNNER="$ROOT/data/training/scripts/phase108_cuda_full_validation.py"
PREFLIGHT="$ROOT/data/training/phase108_scale_candidate_preflight.py"
SCALE_UTIL="$ROOT/data/training/scripts/phase108_scale_utils.py"
HELPER_TEST="$ROOT/data/training/scripts/test_phase108_hf_adapter_smoke.py"
SCALE_TEST="$ROOT/data/training/scripts/test_phase108_lora_scale.py"
MANIFEST="$ROOT/models/phase108-cuda-recovery-scale20-corrected-20260924-r2/manifest.json"
OUT="$ROOT/results/phase108-r2-valid-scale-sweep-$SLURM_JOB_ID.jsonl"

VALIDATION_SHA256=44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365
ADAPTER_SHA256=4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772
BASE_CONFIG_SHA256=260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650
BASE_INDEX_SHA256=5e699a61da09415f33a625885364d3889a80acb6ab88aedaf6e195b2612addf4
RUNNER_SHA256=1f3ede835ac356ca8dea9452aca5fecb21deb430de705f7d1d3afd71c1939414
PREFLIGHT_SHA256=6dd203c476c48ea8475141c278b65be607c59b688c2ae67c018223a8d0e31f6b
SCALE_UTIL_SHA256=966d35d28d3222950c8b1b955838ce36d87f85e9449b53281455381dac4d5849
HELPER_TEST_SHA256=1bb2a735100e7dc79f9472a8536464aff8cbdb524d667697e3288de6d922870f
SCALE_TEST_SHA256=46b730be0d1dd1728a4501d33c77c3ed60cea397428dd8fb16245f886c2e1b69

for path in "$BASE/config.json" "$BASE/model.safetensors.index.json" \
            "$BASE/model-00001-of-00002.safetensors" "$BASE/model-00002-of-00002.safetensors" \
            "$ADAPTER" "$VALIDATION" "$RUNNER" "$PREFLIGHT" "$SCALE_UTIL" \
            "$HELPER_TEST" "$SCALE_TEST" "$MANIFEST"; do
  test -r "$path"
done
test "$(sha256sum "$BASE/config.json" | awk '{print $1}')" = "$BASE_CONFIG_SHA256"
test "$(sha256sum "$BASE/model.safetensors.index.json" | awk '{print $1}')" = "$BASE_INDEX_SHA256"
test "$(sha256sum "$VALIDATION" | awk '{print $1}')" = "$VALIDATION_SHA256"
test "$(sha256sum "$ADAPTER" | awk '{print $1}')" = "$ADAPTER_SHA256"
test "$(sha256sum "$RUNNER" | awk '{print $1}')" = "$RUNNER_SHA256"
test "$(sha256sum "$PREFLIGHT" | awk '{print $1}')" = "$PREFLIGHT_SHA256"
test "$(sha256sum "$SCALE_UTIL" | awk '{print $1}')" = "$SCALE_UTIL_SHA256"
test "$(sha256sum "$HELPER_TEST" | awk '{print $1}')" = "$HELPER_TEST_SHA256"
test "$(sha256sum "$SCALE_TEST" | awk '{print $1}')" = "$SCALE_TEST_SHA256"
test "$(sha256sum "$MANIFEST" | awk '{print $1}')" = e60ae88a3f491ed94b13f9e26ef0892e5986c838f69dff2fcbf8714185a29636

cd "$ROOT/data/training/scripts"
"$PYTHON" -m unittest -v test_phase108_hf_adapter_smoke test_phase108_lora_scale
"$PYTHON" "$PREFLIGHT" --candidate "$(dirname "$MANIFEST")" \
  --expected-input-sha256 3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036

echo "PHASE108_SCALE_VALIDATION_DIAGNOSTIC=true blind=false scored=false promotion=false train_split_read=false test_split_read=false adapter_sha256=$ADAPTER_SHA256 validation_sha256=$VALIDATION_SHA256 wrapper_sha256=$(sha256sum "$0" | awk '{print $1}')"
mkdir -p "$ROOT/results"
test ! -e "$OUT"

for scale in 1.0 2.5 5.0 10.0 20.0; do
  "$PYTHON" -u "$RUNNER" \
    --base "$BASE" --adapter "$ADAPTER" \
    --validation "$VALIDATION" --expected-validation-sha256 "$VALIDATION_SHA256" \
    --expected-adapter-sha256 "$ADAPTER_SHA256" --max-length 2304 \
    --mlx-scale "$scale" | tee -a "$OUT"
done
chmod 600 "$OUT"
sha256sum "$OUT" > "$OUT.sha256"
chmod 600 "$OUT.sha256"
echo "PHASE108_SCALE_VALIDATION_SWEEP=PASS scales=1,2.5,5,10,20 rows_per_scale=1089 output=$OUT output_sha256=$(awk '{print $1}' "$OUT.sha256") production_approval=false"
