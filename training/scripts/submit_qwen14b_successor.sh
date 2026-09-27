#!/usr/bin/env bash
# Submit one transparent successor for the bounded Qwen3-14B service.
# This never starts a second GPU allocation immediately: Slurm holds the
# successor until the current allocation exits.  It deliberately does not
# cancel, renew, or disguise any job.
set -Eeuo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9]+$ ]]; then
  echo "usage: $0 CURRENT_JOB_ID" >&2
  exit 2
fi

CURRENT_JOB_ID=$1
ROOT=${ROOT:-/data3/ieug25/zj225/cyber-model-migration}
SCRIPT="$ROOT/data/training/slurm/qwen14b_dual_api_service.sbatch"

command -v sbatch >/dev/null
test -r "$SCRIPT"

# Refuse to create a dependency on a job that is not ours.  This is a
# read-only ownership check and avoids accidental cross-user dependencies.
OWNER=$(squeue -h -j "$CURRENT_JOB_ID" -o '%u' 2>/dev/null || true)
if [[ -z "$OWNER" ]]; then
  OWNER=$(sacct -n -X -j "$CURRENT_JOB_ID" --format=User%20 2>/dev/null | awk 'NF {print $1; exit}')
fi
if [[ "$OWNER" != "${USER:?USER must be set}" ]]; then
  echo "refusing: job $CURRENT_JOB_ID is not an active/completed job owned by $USER" >&2
  exit 1
fi

echo "Submitting one successor afterany:$CURRENT_JOB_ID (no overlapping allocation)." >&2
exec sbatch --dependency="afterany:$CURRENT_JOB_ID" \
  --export="ALL,HANDOFF_FROM_JOB=$CURRENT_JOB_ID" \
  "$SCRIPT"
