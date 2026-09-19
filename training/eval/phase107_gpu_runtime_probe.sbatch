#!/usr/bin/env bash
# Infrastructure-only probe. It does not load models or run benchmark prompts.
# Submit only to the dedicated GPU-LARGE A100 partition.
#SBATCH --job-name=p107-runtime
#SBATCH --partition=GPU-LARGE
#SBATCH --gres=gpu:A100-40G:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:02:00
#SBATCH --output=phase107-runtime-%j.out

set -u

echo "timestamp=$(date -Is)"
echo "host=$(hostname)"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi -L
  nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv
else
  echo "nvidia-smi: missing"
fi

for tool in python3 python cmake ninja nvcc llama-server llama-cli; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf '%s: %s\n' "$tool" "$(command -v "$tool")"
  else
    printf '%s: missing\n' "$tool"
  fi
done

if command -v conda >/dev/null 2>&1; then
  conda run --no-capture-output -n cyber-cuda python -c 'import torch; print("torch", torch.__version__); print("cuda_available", torch.cuda.is_available()); print("torch_cuda", torch.version.cuda); print("device", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none")' || echo "cyber-cuda torch probe failed"
else
  echo "conda: missing"
fi

echo "probe_complete=true"
