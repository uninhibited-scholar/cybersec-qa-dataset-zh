#!/bin/bash
# Fixed valid-split-only comparison for existing isolated follow-up candidates.
# No training/test split, blind suite, API, deployment, or model writes.
#SBATCH --job-name=p108-follow-val
#SBATCH --partition=GPU-LARGE
#SBATCH --gres=gpu:A100-40G:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-follow-val-%j.log

set -euo pipefail
umask 077
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
VALIDATION="$ROOT/data/phase108-clean-v2/valid.jsonl"
RUNNER="$ROOT/data/training/scripts/phase108_cuda_full_validation.py"
SCALE_UTIL="$ROOT/data/training/scripts/phase108_scale_utils.py"
RUN_DIR="$ROOT/results/phase108-followup-fixed-validation-$SLURM_JOB_ID"

readonly PARENT_SHA=3ed1a85e7b021e1498332a525bfa4bb75b336a03579d526f8210f1576317036
readonly VALIDATION_SHA=44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365
readonly BASE_CONFIG_SHA=260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650
readonly BASE_INDEX_SHA=5e699a61da09415f33a625885364d3889a80acb6ab88aedaf6e195b2612addf4
readonly RUNNER_SHA=1f3ede835ac356ca8dea9452aca5fecb21deb430de705f7d1d3afd71c1939414
readonly SCALE_UTIL_SHA=966d35d28d3222950c8b1b955838ce36d87f85e9449b53281455381dac4d5849

check_file_hash() {
  local file="$1" expected="$2"
  test -r "$file"
  test "$(sha256sum "$file" | awk '{print $1}')" = "$expected"
}

check_file_hash "$VALIDATION" "$VALIDATION_SHA"
check_file_hash "$BASE/config.json" "$BASE_CONFIG_SHA"
check_file_hash "$BASE/model.safetensors.index.json" "$BASE_INDEX_SHA"
check_file_hash "$RUNNER" "$RUNNER_SHA"
check_file_hash "$SCALE_UTIL" "$SCALE_UTIL_SHA"
mkdir -m 700 "$RUN_DIR"

verify_manifest() {
  local name="$1" expected_manifest="$2" expected_adapter="$3" expected_data="$4" expected_steps="$5"
  local candidate="$ROOT/models/$name"
  check_file_hash "$candidate/manifest.json" "$expected_manifest"
  check_file_hash "$candidate/adapters.safetensors" "$expected_adapter"
  "$PYTHON" - "$candidate/manifest.json" "$expected_data" "$expected_steps" "$PARENT_SHA" <<'PY'
import json,sys
m=json.load(open(sys.argv[1])); data=sys.argv[2]; steps=int(sys.argv[3]); parent=sys.argv[4]
assert m["kind"] == "phase108_cuda_recovery_candidate", m
assert m["base"] == "/data3/ieug25/zj225/cyber-model-migration/models/base-phase3-dequantized", m
assert m["base_config_sha256"] == "260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650", m
assert m["input_mlx_adapter_sha256"] == parent, m
assert m["data"].endswith(data), m
assert m["train_rows"] == 19621 and m["test_split_read"] is False, m
assert m["max_steps"] == steps and m["max_length"] == 2304, m
l=m["lora"]
assert (l["rank"],l["mlx_scale"],l["peft_lora_alpha"],l["peft_effective_scale"]) == (8,20.0,160.0,20.0), l
assert l["layers"] == [32,33,34,35], l
print(json.dumps({"manifest_preflight":"pass","data":m["data"],"train_rows":m["train_rows"],"max_steps":m["max_steps"],"input_adapter_sha256":parent,"test_split_read":False},sort_keys=True))
PY
}

run_validation() {
  local name="$1" expected_manifest="$2" expected_adapter="$3" expected_data="$4" expected_steps="$5"
  local candidate="$ROOT/models/$name"
  verify_manifest "$name" "$expected_manifest" "$expected_adapter" "$expected_data" "$expected_steps"
  "$PYTHON" -u "$RUNNER" --base "$BASE" --adapter "$candidate/adapters.safetensors" \
    --validation "$VALIDATION" --expected-validation-sha256 "$VALIDATION_SHA" \
    --expected-adapter-sha256 "$expected_adapter" --max-length 2304 --mlx-scale 20.0 \
    | tee -a "$RUN_DIR/results.jsonl"
}

run_validation phase108-formatmix-20260925 \
  44bf5490b8fcd523e44ed945c5355bfff285f81775f8170bb5358e3304caddaa \
  3c87564c97b003990242b988c72cd8c76a9ccf0f8bfbf1058a106f53e26ef461 \
  phase108-clean-v3-formatmix 7621
run_validation phase108-bare-canary-20260925 \
  e62dd0060670621667fbc1dd4fc508f25ea62f388ac32a07558d38031f7aedf5 \
  5686ee98e8ed09cd31f3f0228dd4cfec60fd58907090b5ec71372c83571f7da4 \
  phase108-clean-v4-bare 1000

chmod 600 "$RUN_DIR/results.jsonl"
echo "fixed_validation_complete=true rows=1089 test_split_read=false production=false output=$RUN_DIR/results.jsonl"
