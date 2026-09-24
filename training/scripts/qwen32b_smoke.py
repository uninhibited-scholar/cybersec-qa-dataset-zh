#!/usr/bin/env python3
import argparse, json, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

parser = argparse.ArgumentParser()
parser.add_argument('--model', required=True)
parser.add_argument('--device', choices=['cuda', 'cpu'], required=True)
args = parser.parse_args()

tok = AutoTokenizer.from_pretrained(args.model)
t0 = time.perf_counter()
if args.device == 'cuda':
    model = AutoModelForCausalLM.from_pretrained(args.model, device_map='auto', torch_dtype='auto')
    target = 'cuda'
else:
    model = AutoModelForCausalLM.from_pretrained(args.model, device_map={'': 'cpu'}, torch_dtype='auto')
    target = 'cpu'
load_s = time.perf_counter() - t0
messages = [{'role': 'user', 'content': '用三句话说明什么是模型评测，以及为什么要保留独立测试集。'}]
inputs = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors='pt')
inputs = inputs.to(target)
if args.device == 'cuda':
    torch.cuda.synchronize()
t1 = time.perf_counter()
with torch.inference_mode():
    out = model.generate(inputs, max_new_tokens=32, do_sample=False)
if args.device == 'cuda':
    torch.cuda.synchronize()
elapsed = time.perf_counter() - t1
text = tok.decode(out[0][inputs.shape[-1]:], skip_special_tokens=True)
new_tokens = int(out.shape[-1] - inputs.shape[-1])
print(json.dumps({'device': args.device, 'load_seconds': load_s, 'generation_seconds': elapsed, 'new_tokens': new_tokens, 'tokens_per_second': new_tokens / elapsed, 'response': text}, ensure_ascii=False))
