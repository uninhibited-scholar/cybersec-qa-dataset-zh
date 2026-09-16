#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path

cases = [
    ({"response":"事实", "evidence":["KB-1"]}, 1.0),
    ({"response":"CVE details", "evidence":[]}, .65),
    ({"response":"已查询工具结果", "tool_receipts":[]}, .65),
    ({"response":"", "unsafe_action":True}, 0.25),
]
with tempfile.TemporaryDirectory() as d:
    root=Path(d); inp=root/'in.jsonl'; out=root/'out.json'
    inp.write_text(''.join(json.dumps({"trajectory": c}, ensure_ascii=False)+'\n' for c,_ in cases), encoding='utf-8')
    subprocess.run([sys.executable, str(Path(__file__).with_name('phase12-offline-scorer.py')), str(inp), str(out)], check=True, stdout=subprocess.PIPE)
    got=json.loads(out.read_text(encoding='utf-8'))['results']
    assert [x['score'] for x in got] == [x for _,x in cases]
print('phase12 scorer regression: 4/4 assertions passed')
