#!/usr/bin/env bash
set -Eeuo pipefail
script=$(cd "$(dirname "$0")" && pwd)/submit_qwen14b_successor.sh
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fake="$tmp/bin"
mkdir "$fake"
cat >"$fake/sbatch" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >"${CAPTURE:?}"
EOF
cat >"$fake/squeue" <<'EOF'
#!/usr/bin/env bash
printf 'zj225\n'
EOF
cat >"$fake/sacct" <<'EOF'
#!/usr/bin/env bash
exit 1
EOF
chmod +x "$fake"/*
out="$tmp/args"
CAPTURE="$out" PATH="$fake:$PATH" USER=zj225 ROOT="$tmp" bash -c '
  mkdir -p "$ROOT/data/training/slurm"
  : > "$ROOT/data/training/slurm/qwen14b_dual_api_service.sbatch"
  "$0" 44601
' "$script"
grep -q -- '--dependency=afterany:44601' "$out"
grep -q -- 'HANDOFF_FROM_JOB=44601' "$out"
echo 'successor submission helper test: PASS'
