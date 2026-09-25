#!/bin/bash
# Base-only cause isolation on a previously exposed sample; diagnostic only.
# No prompts/answers in logs; output contains IDs, hashes, lengths, timings.
#SBATCH --job-name=p108-base-only
#SBATCH --partition=GPU-MEDIUM
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:45:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-base-only-%j.log

set -euo pipefail
umask 077
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
CASES="$ROOT/data/phase108-eval-private-v09/phase108-private-cases-v0.9.json"
REPLAY="$ROOT/data/training/phase108_replay_diagnostic.py"
BASE_RUNNER="$ROOT/data/training/phase108_base_only_replay.py"
OUT="$ROOT/results/phase108-v09-base-only-$SLURM_JOB_ID.jsonl"

readonly CASES_SHA256=9a4d398893034b922cc67582089642c553733c856ab2812088b398a2546fbb6b
readonly REPLAY_SHA256=c4b3744cb951f24c3d51fe087c8fb36b8953e8d7391baf3862967a56508118ea
readonly BASE_RUNNER_SHA256=3585e9f620ed43cd2d58b77a26ccd65179b21dfff0f0646d821a58fbe329f3ed
readonly BASE_CONFIG_SHA256=260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650
readonly TOKENIZER_JSON_SHA256=aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4
readonly TOKENIZER_CONFIG_SHA256=1089e6487eb96a3c3827ecd2c90c705c6da169ebd1124d59c82f1ff06b8e9f73
readonly SHARD1_SHA256=25094f7fbaef4769da447cb6ebf4a39d99ccc5043856cce1b4f8fc2f91ed9115
readonly SHARD2_SHA256=a2fd70328fc4fb518bb40ac806e8c05f21ad12e228648684775f67c28104815d

for path in "$BASE/config.json" "$BASE/tokenizer.json" "$BASE/tokenizer_config.json" \
  "$BASE/model-00001-of-00002.safetensors" "$BASE/model-00002-of-00002.safetensors" \
  "$CASES" "$REPLAY" "$BASE_RUNNER"; do test -r "$path"; done
test "$(sha256sum "$BASE/config.json" | awk '{print $1}')" = "$BASE_CONFIG_SHA256"
test "$(sha256sum "$BASE/tokenizer.json" | awk '{print $1}')" = "$TOKENIZER_JSON_SHA256"
test "$(sha256sum "$BASE/tokenizer_config.json" | awk '{print $1}')" = "$TOKENIZER_CONFIG_SHA256"
test "$(sha256sum "$BASE/model-00001-of-00002.safetensors" | awk '{print $1}')" = "$SHARD1_SHA256"
test "$(sha256sum "$BASE/model-00002-of-00002.safetensors" | awk '{print $1}')" = "$SHARD2_SHA256"
test "$(sha256sum "$CASES" | awk '{print $1}')" = "$CASES_SHA256"
test "$(sha256sum "$REPLAY" | awk '{print $1}')" = "$REPLAY_SHA256"
test "$(sha256sum "$BASE_RUNNER" | awk '{print $1}')" = "$BASE_RUNNER_SHA256"
"$PYTHON" -m py_compile "$BASE_RUNNER" "$REPLAY"
"$PYTHON" "$BASE_RUNNER" --base "$BASE" --cases "$CASES" \
  --expected-cases-sha256 "$CASES_SHA256" --preflight-only
test ! -e "$OUT"
mkdir -p "$ROOT/results"

echo "BASE_ONLY_REPLAY_DIAGNOSTIC=true blind=false score=false promotion=false tools=[]"
echo "base_config_sha256=$BASE_CONFIG_SHA256 shard1=$SHARD1_SHA256 shard2=$SHARD2_SHA256"
"$PYTHON" -u "$BASE_RUNNER" --base "$BASE" --cases "$CASES" \
  --expected-cases-sha256 "$CASES_SHA256" --output "$OUT" \
  --device cpu --max-new-tokens 1
chmod 600 "$OUT"
sha256sum "$OUT" >"$OUT.sha256"
chmod 600 "$OUT.sha256"
echo "BASE_ONLY_REPLAY_COMPLETE=true output=$OUT"
