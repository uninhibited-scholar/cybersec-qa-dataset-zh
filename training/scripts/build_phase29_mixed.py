import json, random
from pathlib import Path

SOURCE = Path('/Users/jiehan/datasets/cybersec-phase24-depth')
FORMAT = Path('/Users/jiehan/datasets/cybersec-phase28-format')
OUT = Path('/Users/jiehan/datasets/cybersec-phase29-mixed')

def read(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]

def main():
    professional = read(SOURCE/'train.jsonl')
    fmt = read(FORMAT/'train.jsonl')
    rng = random.Random(20261023)
    rng.shuffle(professional); rng.shuffle(fmt)
    # Keep professional coverage dominant; repeat each format row once only.
    rows = professional + fmt[:min(len(fmt), 48)]
    rng.shuffle(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    v = read(SOURCE/'valid.jsonl') + read(FORMAT/'valid.jsonl')
    t = read(SOURCE/'test.jsonl') + read(FORMAT/'test.jsonl')
    for name, part in [('train', rows), ('valid', v), ('test', t)]:
        (OUT/f'{name}.jsonl').write_text('\n'.join(json.dumps(x, ensure_ascii=False) for x in part)+'\n')
    print(json.dumps({'train':len(rows),'valid':len(v),'test':len(t)}))
if __name__ == '__main__': main()
