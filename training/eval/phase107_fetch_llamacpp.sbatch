#!/usr/bin/env bash
# Fetch and verify the official prebuilt llama.cpp CUDA 12.8 runtime.
# Short A100 packaging step; no model or benchmark data is loaded.
#SBATCH --job-name=p107-fetch-llama
#SBATCH --partition=GPU-LARGE
#SBATCH --gres=gpu:A100-40G:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:05:00
#SBATCH --output=phase107-llamacpp-fetch-%j.out

set -euo pipefail

readonly TAG="b11046"
readonly ASSET="llama-b11046-bin-ubuntu-cuda-12.8-x64.tar.gz"
readonly URL="https://github.com/ggml-org/llama.cpp/releases/download/${TAG}/${ASSET}"
readonly EXPECTED_SHA256="c27982438017c508721d8a38acedd6c746edac9c7b58517fe9a055cb61292c8a"
readonly RUNTIME_ROOT="$HOME/cyber-model-migration/phase107-runtime"
readonly ARCHIVE="$RUNTIME_ROOT/$ASSET"
readonly INSTALL_DIR="$RUNTIME_ROOT/llama-${TAG}-cuda-12.8-x64"

echo "timestamp=$(date -Is)"
echo "host=$(hostname)"
echo "os=$(sed -n 's/^PRETTY_NAME=//p' /etc/os-release 2>/dev/null | tr -d '\"')"

mkdir -p "$RUNTIME_ROOT"
if [[ -e "$INSTALL_DIR" ]]; then
  echo "refusing to overwrite existing install: $INSTALL_DIR" >&2
  exit 2
fi

if [[ ! -s "$ARCHIVE" ]]; then
  TEMP_ARCHIVE="${ARCHIVE}.partial-${SLURM_JOB_ID:-manual}"
  if [[ -e "$TEMP_ARCHIVE" ]]; then
    echo "refusing to overwrite partial archive: $TEMP_ARCHIVE" >&2
    exit 2
  fi
  curl --fail --location --retry 3 --connect-timeout 10 --max-time 300 "$URL" --output "$TEMP_ARCHIVE"
  printf '%s  %s\n' "$EXPECTED_SHA256" "$TEMP_ARCHIVE" | sha256sum --check --status
  mv "$TEMP_ARCHIVE" "$ARCHIVE"
fi

printf '%s  %s\n' "$EXPECTED_SHA256" "$ARCHIVE" | sha256sum --check --status
echo "sha256_verified=$EXPECTED_SHA256"

mkdir "$INSTALL_DIR"
tar -tzf "$ARCHIVE" >/dev/null
tar --no-same-owner -xzf "$ARCHIVE" -C "$INSTALL_DIR"
echo "install_dir=$INSTALL_DIR"
du -sh "$ARCHIVE" "$INSTALL_DIR"
find "$INSTALL_DIR" -maxdepth 3 -type f \( -name 'llama-server' -o -name 'llama-cli' -o -name 'llama' \) -print

SERVER_BIN="$(find "$INSTALL_DIR" -type f -name 'llama-server' -print -quit)"
if [[ -n "$SERVER_BIN" ]]; then
  echo "server_binary=$SERVER_BIN"
  CUDA_LIB_ROOT="$HOME/miniforge3/envs/cyber-cuda/lib/python3.11/site-packages/nvidia"
  CUDA_LIB_PATH=""
  for libdir in "$CUDA_LIB_ROOT"/*/lib; do
    if [[ -d "$libdir" ]]; then
      CUDA_LIB_PATH="${CUDA_LIB_PATH:+$CUDA_LIB_PATH:}$libdir"
    fi
  done
  export LD_LIBRARY_PATH="${CUDA_LIB_PATH}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  echo "cuda_library_paths=${CUDA_LIB_PATH:-none}"
  ldd "$SERVER_BIN" || true
  "$SERVER_BIN" --version || true
else
  echo "llama-server binary not found in verified release archive" >&2
  exit 3
fi
