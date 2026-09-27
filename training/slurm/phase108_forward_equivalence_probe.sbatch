#!/bin/bash
# Isolated forward-math comparison only; no generation, eval suite, or API.
# The job runs all large-file hashes and model inference on the GPU node.
#SBATCH --job-name=p108-fwd-equiv
#SBATCH --partition=GPU-TITANX
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=20G
#SBATCH --time=00:40:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-forward-equivalence-%j.log

set -euo pipefail
umask 077
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
ADAPTER="$ROOT/models/phase108-cuda-recovery-scale20-corrected-20260924-r2/adapters.safetensors"
PROBE="$ROOT/data/training/scripts/phase108_forward_equivalence_probe.py"
MANUAL_LOADER="$ROOT/data/training/scripts/phase108_hf_adapter_smoke.py"
PEFT_LOADER="$ROOT/data/training/scripts/phase108_cuda_full_validation.py"
UNIT_TEST="$ROOT/data/training/scripts/test_phase108_hf_adapter_smoke.py"

ADAPTER_SHA=4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772
BASE_CONFIG_SHA=260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650
BASE_INDEX_SHA=5e699a61da09415f33a625885364d3889a80acb6ab88aedaf6e195b2612addf4
BASE_SHARD1_SHA=25094f7fbaef4769da447cb6ebf4a39d99ccc5043856cce1b4f8fc2f91ed9115
BASE_SHARD2_SHA=a2fd70328fc4fb518bb40ac806e8c05f21ad12e228648684775f67c28104815d
PROBE_SHA=271f21663af9116fc06565c189865492907a37fa443d766a97902587e937a5a1
MANUAL_LOADER_SHA=00ef5d3b1aaada8285b711a68f47c9e00a4fb9dbbd993e8eaf8eefd7426fa371
PEFT_LOADER_SHA=1f3ede835ac356ca8dea9452aca5fecb21deb430de705f7d1d3afd71c1939414
UNIT_TEST_SHA=1bb2a735100e7dc79f9472a8536464aff8cbdb524d667697e3288de6d922870f

for path in "$BASE/config.json" "$BASE/model.safetensors.index.json" \
            "$BASE/model-00001-of-00002.safetensors" "$BASE/model-00002-of-00002.safetensors" \
            "$ADAPTER" "$PROBE" "$MANUAL_LOADER" "$PEFT_LOADER" "$UNIT_TEST"; do
  test -r "$path"
done
test "$(sha256sum "$BASE/config.json" | awk '{print $1}')" = "$BASE_CONFIG_SHA"
test "$(sha256sum "$BASE/model.safetensors.index.json" | awk '{print $1}')" = "$BASE_INDEX_SHA"
test "$(sha256sum "$BASE/model-00001-of-00002.safetensors" | awk '{print $1}')" = "$BASE_SHARD1_SHA"
test "$(sha256sum "$BASE/model-00002-of-00002.safetensors" | awk '{print $1}')" = "$BASE_SHARD2_SHA"
test "$(sha256sum "$ADAPTER" | awk '{print $1}')" = "$ADAPTER_SHA"
test "$(sha256sum "$PROBE" | awk '{print $1}')" = "$PROBE_SHA"
test "$(sha256sum "$MANUAL_LOADER" | awk '{print $1}')" = "$MANUAL_LOADER_SHA"
test "$(sha256sum "$PEFT_LOADER" | awk '{print $1}')" = "$PEFT_LOADER_SHA"
test "$(sha256sum "$UNIT_TEST" | awk '{print $1}')" = "$UNIT_TEST_SHA"

cd "$ROOT/data/training/scripts"
"$PYTHON" -m unittest -v test_phase108_hf_adapter_smoke
"$PYTHON" -u "$PROBE" --base "$BASE" --adapter "$ADAPTER" \
  --expected-adapter-sha256 "$ADAPTER_SHA" \
  --expected-base-config-sha256 "$BASE_CONFIG_SHA"
echo "PHASE108_FORWARD_EQUIVALENCE=COMPLETE generation_performed=false production_changed=false"
