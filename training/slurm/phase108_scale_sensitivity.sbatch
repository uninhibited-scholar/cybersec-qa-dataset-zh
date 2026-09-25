#!/bin/bash
# CPU-only scale sensitivity diagnostic on a previously exposed sample.
# No raw prompt/answer is written; no GPU resource is requested.
#SBATCH --job-name=p108-scale-probe
#SBATCH --partition=GPU-MEDIUM
#SBATCH --nodelist=dell3090
#SBATCH --cpus-per-task=4
#SBATCH --mem=20G
#SBATCH --time=00:45:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-scale-probe-%j.log

set -euo pipefail
umask 077
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
PARENT="$ROOT/models/phase108-step12000-20260920/0012000_adapters.safetensors"
CANDIDATE="$ROOT/models/phase108-cuda-recovery-scale20-corrected-20260924-r2/adapters.safetensors"
CASES="$ROOT/data/phase108-eval-private-v09/phase108-private-cases-v0.9.json"
RUNNER="$ROOT/data/training/phase108_scale_sensitivity.py"
REPLAY="$ROOT/data/training/phase108_replay_diagnostic.py"
HELPER="$ROOT/data/training/phase108_hf_adapter_smoke.py"
OUT="$ROOT/results/phase108-v09-scale-sensitivity-$SLURM_JOB_ID.jsonl"

readonly CASES_SHA256=9a4d398893034b922cc67582089642c553733c856ab2812088b398a2546fbb6b
readonly PARENT_SHA256=3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036
readonly CANDIDATE_SHA256=4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772
readonly RUNNER_SHA256=9edb367ba8255c86164c87e61dd0f6e283e211d78899a4191c3676284758833b
readonly REPLAY_SHA256=c4b3744cb951f24c3d51fe087c8fb36b8953e8d7391baf3862967a56508118ea
readonly HELPER_SHA256=00ef5d3b1aaada8285b711a68f47c9e00a4fb9dbbd993e8eaf8eefd7426fa371

for path in "$BASE/config.json" "$PARENT" "$CANDIDATE" "$CASES" "$RUNNER" "$REPLAY" "$HELPER"; do test -r "$path"; done
test "$(sha256sum "$PARENT" | awk '{print $1}')" = "$PARENT_SHA256"
test "$(sha256sum "$CANDIDATE" | awk '{print $1}')" = "$CANDIDATE_SHA256"
test "$(sha256sum "$CASES" | awk '{print $1}')" = "$CASES_SHA256"
test "$(sha256sum "$RUNNER" | awk '{print $1}')" = "$RUNNER_SHA256"
test "$(sha256sum "$REPLAY" | awk '{print $1}')" = "$REPLAY_SHA256"
test "$(sha256sum "$HELPER" | awk '{print $1}')" = "$HELPER_SHA256"
"$PYTHON" -m py_compile "$RUNNER" "$REPLAY" "$HELPER"
"$PYTHON" "$RUNNER" --base "$BASE" --parent "$PARENT" --candidate "$CANDIDATE" \
  --cases "$CASES" --expected-cases-sha256 "$CASES_SHA256" \
  --expected-parent-sha256 "$PARENT_SHA256" \
  --expected-candidate-sha256 "$CANDIDATE_SHA256" --device cpu --preflight-only
test ! -e "$OUT"
mkdir -p "$ROOT/results"
echo "SCALE_SENSITIVITY_DIAGNOSTIC=true blind=false score=false promotion=false tools=[]"
"$PYTHON" -u "$RUNNER" --base "$BASE" --parent "$PARENT" --candidate "$CANDIDATE" \
  --cases "$CASES" --expected-cases-sha256 "$CASES_SHA256" \
  --expected-parent-sha256 "$PARENT_SHA256" \
  --expected-candidate-sha256 "$CANDIDATE_SHA256" --device cpu \
  --max-new-tokens 16 --output "$OUT"
chmod 600 "$OUT"
sha256sum "$OUT" >"$OUT.sha256"
chmod 600 "$OUT.sha256"
echo "SCALE_SENSITIVITY_COMPLETE=true output=$OUT"
