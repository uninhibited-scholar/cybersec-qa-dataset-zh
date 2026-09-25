#!/bin/bash
# Re-run fixed full validation with the candidate's actual MLX scale (20).
# Sequential checkpoints share one allocation; only valid.jsonl is read.
# No training, test split, blind-set, production, or deployment path.
#SBATCH --job-name=p108-r2-valscale20
#SBATCH --partition=GPU-MEDIUM
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/phase108-r2-valscale20-%j.log

set -euo pipefail
umask 077
ROOT=/data3/ieug25/zj225/cyber-model-migration
PYTHON=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
BASE="$ROOT/models/base-phase3-dequantized"
CANDIDATE_DIR="$ROOT/models/phase108-cuda-recovery-scale20-corrected-20260924-r2"
VALIDATION="$ROOT/data/phase108-clean-v2/valid.jsonl"
VALIDATION_SHA256=44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365
BASE_CONFIG_SHA256=260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650
INPUT_ADAPTER_SHA256=3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036
RUNNER="$ROOT/data/training/scripts/phase108_cuda_full_validation.py"
PREFLIGHT="$ROOT/data/training/phase108_scale_candidate_preflight.py"
SCALE_UTIL="$ROOT/data/training/scripts/phase108_scale_utils.py"
EXPECTED_RUNNER_SHA256=8ca10ad8fc39e9346728025d53da505eb90366fcfa67a074dfff0bcfc65d51e4
EXPECTED_PREFLIGHT_SHA256=6dd203c476c48ea8475141c278b65be607c59b688c2ae67c018223a8d0e31f6b
EXPECTED_SCALE_UTIL_SHA256=0988df335a3d563587d090f5b6eb967f755d2747b62972b8deff7e2b20f87a47
EXPECTED_MANIFEST_SHA256=e60ae88a3f491ed94b13f9e26ef0892e5986c838f69dff2fcbf8714185a29636
EXPECTED_BASE_INDEX_SHA256=5e699a61da09415f33a625885364d3889a80acb6ab88aedaf6e195b2612addf4
OUT="$ROOT/results/phase108-r2-fixed-scale-validation-$SLURM_JOB_ID.jsonl"

test -r "$BASE/config.json" -a -r "$VALIDATION" -a -r "$RUNNER" -a -r "$PREFLIGHT" -a -r "$SCALE_UTIL"
test "$(sha256sum "$BASE/config.json" | awk '{print $1}')" = "$BASE_CONFIG_SHA256"
test "$(sha256sum "$BASE/model.safetensors.index.json" | awk '{print $1}')" = "$EXPECTED_BASE_INDEX_SHA256"
test "$(sha256sum "$VALIDATION" | awk '{print $1}')" = "$VALIDATION_SHA256"
test "$(sha256sum "$RUNNER" | awk '{print $1}')" = "$EXPECTED_RUNNER_SHA256"
test "$(sha256sum "$PREFLIGHT" | awk '{print $1}')" = "$EXPECTED_PREFLIGHT_SHA256"
test "$(sha256sum "$SCALE_UTIL" | awk '{print $1}')" = "$EXPECTED_SCALE_UTIL_SHA256"
test "$(sha256sum "$CANDIDATE_DIR/manifest.json" | awk '{print $1}')" = "$EXPECTED_MANIFEST_SHA256"
"$PYTHON" "$PREFLIGHT" --candidate "$CANDIDATE_DIR" --expected-input-sha256 "$INPUT_ADAPTER_SHA256"
echo "BASE_MODEL_SHARD_HASHES_BEGIN"
sha256sum "$BASE/model-00001-of-00002.safetensors" "$BASE/model-00002-of-00002.safetensors"
echo "BASE_MODEL_SHARD_HASHES_END"
mkdir -p "$ROOT/results"
test ! -e "$OUT"

while IFS=$'\t' read -r checkpoint expected_sha256; do
  [[ -n "$checkpoint" ]] || continue
  adapter="$CANDIDATE_DIR/$checkpoint"
  test -r "$adapter"
  test "$(sha256sum "$adapter" | awk '{print $1}')" = "$expected_sha256"
  "$PYTHON" -u "$RUNNER" \
    --base "$BASE" --adapter "$adapter" \
    --validation "$VALIDATION" --expected-validation-sha256 "$VALIDATION_SHA256" \
    --expected-adapter-sha256 "$expected_sha256" --max-length 2304 --mlx-scale 20.0 \
    | tee -a "$OUT"
done <<'CHECKPOINTS'
0000001_adapters.safetensors	7f1024dc51019a7114dfa32874b41f513161b3aff59756e59c3f49725ec22759
0001000_adapters.safetensors	f7754bddcfc40293964ed95d077cb68864a7f8a4f5c7e5627615f54d492d7e9a
0002000_adapters.safetensors	d7684d1d5df985924e614b8258cc0d5d65254897ce6d68ca481e9726c5d4273c
0003000_adapters.safetensors	528841ff0e0280cd563facadfbf1fd699332e4b673307159830ba980bda1ad5a
0004000_adapters.safetensors	5d21fcb8bd04ccffae3c0393a702a633462f02d64557d9ac97a3b015a714ff24
0005000_adapters.safetensors	6a467b1c01c0d8da5a3c2eabe5a8c2499e887004088d94a262722dbea86fbf63
0006000_adapters.safetensors	02aa967835d37994481f2a8393dd212d1689d321f40732a5c850adf0b6e5c8d9
0007000_adapters.safetensors	62acbdc57011ea5a4927514c6868549d98ae36501ddbefab847424cb4ebe66ed
adapters.safetensors	4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772
CHECKPOINTS

echo "PHASE108_FIXED_SCALE_VALIDATION=PASS rows_per_checkpoint=1089 effective_scale=20 test_split_read=false production_approval=false output=$OUT"
