"""Create a non-destructive model view and verify actual MLX masked tokens."""
import hashlib
import json
from pathlib import Path
from mlx_lm import load
from mlx_lm.tuner.datasets import ChatDataset

root = Path('/Users/jiehan')
source = root/'models/Qwen3-4B-mlx-4bit'
target = root/'models/Qwen3-4B-official-chatml-phase9'
official_path = root/'cyber-agent/qwen3-official-tokenizer-config.json'
assert hashlib.sha256(official_path.read_bytes()).hexdigest() == 'd5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101'
official = json.loads(official_path.read_text())
target.mkdir(exist_ok=False)
for item in source.iterdir():
    if item.name == 'tokenizer_config.json':
        config = json.loads(item.read_text())
        config['chat_template'] = '{% set enable_thinking = false %}' + official['chat_template']
        (target/item.name).write_text(json.dumps(config, ensure_ascii=False, indent=2))
    else:
        (target/item.name).symlink_to(item)
model, tok = load(str(target))
rows = []
for split in ('train','valid'):
    rows += [json.loads(line) for line in (root/f'datasets/phase8-neutral-pilot-20260908/{split}.jsonl').read_text().splitlines()]
dataset = ChatDataset(rows, tok, mask_prompt=True)
lengths = []
for row in rows:
    tokens, offset = dataset.process(row)
    prefix = tok.apply_chat_template(row['messages'][:-1], add_generation_prompt=True, return_dict=False)
    assert tokens[:offset] == prefix, 'Masked prefix does not match generation prefix'
    assert 0 < offset < len(tokens) <= 512
    answer = tok.decode(tokens[offset:])
    assert row['messages'][-1]['content'] in answer, 'Answer not fully included'
    lengths.append(len(tokens))
probe = tok.apply_chat_template([{'role':'system','content':'SYSTEM_SENTINEL'}, {'role':'user','content':'USER_SENTINEL'}],tokenize=False,add_generation_prompt=True)
assert '<|im_start|>system\nSYSTEM_SENTINEL<|im_end|>' in probe
assert '<|im_start|>user\nUSER_SENTINEL<|im_end|>' in probe
print(json.dumps({'verified_rows':len(rows),'max_tokens':max(lengths),'masked_prefix_matches':True,'roles_preserved':True,'model_view':str(target)}))
