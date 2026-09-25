#!/bin/bash
# Compare the exact Phase108 parent adapter to its trained continuation under
# the same frozen validation implementation. This does not train or promote.
# Only the frozen valid.jsonl split is read; no prompts/responses are emitted.
#SBATCH --job-name=p108-parent-val20
#SBATCH --partition=GPU-MEDIUM
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-parent-val20-%j.log

set -euo pipefail
umask 077
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
PARENT="$ROOT/models/phase108-step12000-20260920/0012000_adapters.safetensors"
PARENT_CONFIG="$ROOT/models/phase108-step12000-20260920/adapter_config.json"
VALIDATION="$ROOT/data/phase108-clean-v2/valid.jsonl"
RUNNER="$ROOT/data/training/scripts/phase108_cuda_full_validation.py"
SCALE_UTIL="$ROOT/data/training/scripts/phase108_scale_utils.py"
OUT="$ROOT/results/phase108-parent-fixed-scale-validation-$SLURM_JOB_ID.jsonl"

readonly PARENT_SHA256=3ed1a85e7b021e1498332a525bfa4bb75b336a03579d526f8210f1576317036
readonly CONFIG_SHA256=daab3b77887c40860fd4b73871b6c6ff18657586acac9d4ff5be26a749d7c0df
readonly VALIDATION_SHA256=44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365
readonly BASE_CONFIG_SHA256=260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650
readonly BASE_INDEX_SHA256=5e699a61da09415f33a625885364d3889a80acb6ab88aedaf6e195b2612addf4
readonly RUNNER_SHA256=1f3ede835ac356ca8dea9452aca5fecb21deb430de705f7d1d3afd71c1939414
readonly SCALE_UTIL_SHA256=966d35d28d3222950c8b1b955838ce36d87f85e9449b53281455381dac4d5849

for path in "$BASE/config.json" "$BASE/model.safetensors.index.json" \
  "$PARENT" "$PARENT_CONFIG" "$VALIDATION" "$RUNNER" "$SCALE_UTIL"; do
  test -r "$path"
done
test "$(sha256sum "$PARENT" | awk '{print $1}')" = "$PARENT_SHA256"
test "$(sha256sum "$PARENT_CONFIG" | awk '{print $1}')" = "$CONFIG_SHA256"
test "$(sha256sum "$VALIDATION" | awk '{print $1}')" = "$VALIDATION_SHA256"
test "$(sha256sum "$BASE/config.json" | awk '{print $1}')" = "$BASE_CONFIG_SHA256"
test "$(sha256sum "$BASE/model.safetensors.index.json" | awk '{print $1}')" = "$BASE_INDEX_SHA256"
test "$(sha256sum "$RUNNER" | awk '{print $1}')" = "$RUNNER_SHA256"
test "$(sha256sum "$SCALE_UTIL" | awk '{print $1}')" = "$SCALE_UTIL_SHA256"
"$PYTHON" - "$PARENT_CONFIG" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1]))
params = cfg.get("lora_parameters", {})
assert params.get("rank") == 8, params
assert params.get("scale") == 20.0, params
assert cfg.get("train") is True and cfg.get("test") is True, cfg
print("PARENT_CONFIG_PREFLIGHT=PASS rank=8 mlx_scale=20.0; validation runner reads only valid.jsonl")
PY
mkdir -p "$ROOT/results"
test ! -e "$OUT"
"$PYTHON" -u "$RUNNER" \
  --base "$BASE" --adapter "$PARENT" \
  --validation "$VALIDATION" --expected-validation-sha256 "$VALIDATION_SHA256" \
  --expected-adapter-sha256 "$PARENT_SHA256" --max-length 2304 --mlx-scale 20.0 \
  | tee "$OUT"
echo "PHASE108_PARENT_FIXED_SCALE_VALIDATION=PASS output=$OUT"
