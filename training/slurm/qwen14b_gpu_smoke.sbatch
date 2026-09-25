#!/bin/bash
# Isolated Qwen3-14B BF16 load/generation smoke test.
#SBATCH --job-name=qwen14b-smoke
#SBATCH --partition=GPU-MEDIUM
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:15:00
#SBATCH --output=/data3/ieug25/zj225/cyber-model-migration/logs/qwen14b-smoke-%j.log
set -euo pipefail
PY=/data3/ieug25/zj225/miniforge3/envs/coevo/bin/python
MODEL=/data3/ieug25/zj225/models/Qwen3-14B-BF16
"$PY" - "$MODEL" <<'PY'
import sys, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
p=sys.argv[1]
t=AutoTokenizer.from_pretrained(p,local_files_only=True)
m=AutoModelForCausalLM.from_pretrained(p,torch_dtype=torch.bfloat16,device_map="cuda:0",local_files_only=True)
rendered=t.apply_chat_template([{"role":"user","content":"用一句话说明最小权限原则。"}],tokenize=False,add_generation_prompt=True)
e=t(rendered,return_tensors="pt").to("cuda")
with torch.inference_mode(): y=m.generate(**e,max_new_tokens=32,do_sample=False)
out=t.decode(y[0,e["input_ids"].shape[1]:],skip_special_tokens=True)
print("generated_tokens=",int(y.shape[1]-e["input_ids"].shape[1]))
print("nonempty=",bool(out.strip()))
PY
