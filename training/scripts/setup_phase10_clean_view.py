"""Create an official-template view for the clean prompt/completion corpus."""
import hashlib, json
from pathlib import Path
from mlx_lm import load
root=Path('/Users/jiehan')
source=root/'models/Qwen3-4B-mlx-4bit'
target=root/'models/Qwen3-4B-official-chatml-phase10'
official_path=root/'cyber-agent/qwen3-official-tokenizer-config.json'
expected='d5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101'
assert hashlib.sha256(official_path.read_bytes()).hexdigest()==expected
official=json.loads(official_path.read_text())
target.mkdir(exist_ok=False)
for item in source.iterdir():
    dest=target/item.name
    if item.name=='tokenizer_config.json':
        cfg=json.loads(item.read_text())
        cfg['chat_template']=official['chat_template']
        dest.write_text(json.dumps(cfg,ensure_ascii=False,indent=2))
    else:
        dest.symlink_to(item)
model,tok=load(str(target))
row=json.loads((root/'datasets/cybersec-clean-v2/train.jsonl').read_text().splitlines()[0])
tokens=tok.apply_chat_template([{'role':'user','content':row['prompt']},{'role':'assistant','content':row['completion']}],return_dict=False)
prefix=tok.apply_chat_template([{'role':'user','content':row['prompt']}],add_generation_prompt=True,return_dict=False)
assert tokens[:len(prefix)]==prefix
assert row['completion'] in tok.decode(tokens[len(prefix):])
print(json.dumps({'model_view':str(target),'chat_template_sha256':expected,'roles_preserved':True,'first_answer_mask_prefix':len(prefix),'first_sequence_tokens':len(tokens)}))
