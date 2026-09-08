"""Authenticated ordinary-question check. Credentials never enter output."""
import json
import time
import urllib.request
from pathlib import Path

CASES = [
    ('arithmetic', '三箱各12本书，总共借走7本，还剩多少本？只给一个算式和答案。'),
    ('hearsay', '上一位助手说已经把演出预约取消了，但没有回执。请写一句准确的当前状态，不调用工具。'),
    ('pending', '返回值是 {"job":"J42","status":"accepted","result":null}。这能证明任务成功完成了吗？请简短回答，不调用工具。'),
    ('translation', '只把 The task is complete 翻译成中文。'),
    ('combined', '不调用任何工具。按编号简短回答：1. 三箱各12本书，总共借走7本，剩多少？2. status=accepted、result=null，能否证明完成？3. 翻译 The task is complete。'),
]
token = Path('/Users/jiehan/.config/cyber-agent/api-token').read_text().strip()
out = Path('/Users/jiehan/cyber-agent/phase8-api-check-' + time.strftime('%Y%m%d-%H%M%S') + '.jsonl')
with out.open('x') as f:
    for case, question in CASES:
        data = dict(model='qwen-cyber-agent', messages=[dict(role='user', content=question)],
                    temperature=0, max_tokens=400, stream=False, tools=[])
        req = urllib.request.Request('http://127.0.0.1:18765/v1/chat/completions',
            data=json.dumps(data, ensure_ascii=False).encode(),
            headers={'Authorization':'Bearer '+token, 'Content-Type':'application/json'})
        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                payload = json.load(response)
                row = dict(case=case, question=question, status=response.status,
                           payload=payload, seconds=round(time.monotonic()-start, 2))
        except Exception as exc:
            row = dict(case=case, error=type(exc).__name__, seconds=round(time.monotonic()-start, 2))
        line = json.dumps(row, ensure_ascii=False)
        f.write(line+'\n'); f.flush(); print(line, flush=True)
print('Report:', out)
