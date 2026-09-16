import json, time, urllib.request
from pathlib import Path

CASES = [
    ("capital", "法国的首都是哪里？"),
    ("math", "2+2等于多少？"),
    ("free", "用一句话解释什么是缓存。"),
    ("json", "只输出 JSON：风险为低。"),
    ("cyber", "请从防御角度说明 SSRF 的验证要点。"),
]

def ask(port, prompt):
    body = json.dumps({"model":"qwen-cyber-local", "messages":[{"role":"user","content":prompt}], "max_tokens":256}).encode()
    token = Path.home().joinpath(".config/cyber-agent/api-token").read_text().strip()
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions", data=body, headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=30) as res:
        payload=json.loads(res.read()); choice=payload["choices"][0]
        return {"text":choice["message"].get("content", ""), "finish_reason":choice.get("finish_reason")}

rows=[]
for kind,prompt in CASES:
    row={"kind":kind,"prompt":prompt}
    for label,port in (("phase69",18766),("phase68",18767)):
        started=time.time()
        try: row[label]={**ask(port,prompt),"elapsed_s":round(time.time()-started,2)}
        except Exception as exc: row[label]={"error":type(exc).__name__,"elapsed_s":round(time.time()-started,2)}
    rows.append(row)
Path("phase69-regression.json").write_text(json.dumps({"phase":69,"timeout_s":30,"production_touched":False,"results":rows},ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"count":len(rows),"report":"phase69-regression.json"},ensure_ascii=False))
