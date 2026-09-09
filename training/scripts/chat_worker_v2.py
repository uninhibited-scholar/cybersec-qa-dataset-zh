"""Candidate worker: official chat template, preserved roles, no output rewriting."""
import json
import os
import sys
from pathlib import Path
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler

def render_prompt(tokenizer, messages, tools):
    if not messages or any(m.get('role') not in {'system','user','assistant','tool'} for m in messages):
        raise ValueError('Unsupported or empty messages')
    # Preserve the caller's system prompt, history, and tool results verbatim.
    return tokenizer.apply_chat_template(messages, tools=tools or None,
        tokenize=False, add_generation_prompt=True, enable_thinking=False)

def main():
    adapter = os.environ.get('CYBER_ADAPTER_PATH') or None
    model, tokenizer = load(os.environ['CYBER_MODEL_PATH'], adapter_path=adapter)
    official = json.loads(Path('/Users/jiehan/cyber-agent/qwen3-official-tokenizer-config.json').read_text())
    tokenizer.chat_template = official['chat_template']
    print(json.dumps({'ready': True}), flush=True)
    for raw in sys.stdin:
        try:
            req = json.loads(raw)
            prompt = render_prompt(tokenizer, req.get('messages'), req.get('tools'))
            answer = generate(model, tokenizer, prompt=prompt,
                max_tokens=max(1, min(int(req.get('max_tokens', 400)), 1400)),
                sampler=make_sampler(temp=float(req.get('temperature', 0))), verbose=False)
            result = {'ok': True, 'answer': answer}
        except Exception as exc:
            result = {'ok': False, 'error': str(exc)}
        print(json.dumps(result, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
