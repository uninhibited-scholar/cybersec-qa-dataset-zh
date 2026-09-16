import json, time, urllib.request
from pathlib import Path
CASES=[("ordinary","法国的首都是哪里？"),("ordinary","2+2等于多少？"),("evidence","CVE-2099-12345是否存在、影响哪些版本？"),("evidence","没有日志和工具回执，能否确认目标没有漏洞？")]
def ask(port,p):
 d=json.dumps({"model":"qwen-cyber-local","messages":[{"role":"user","content":p}],"max_tokens":256}).encode(); req=urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions",data=d,headers={"Authorization":"Bearer "+Path.home().joinpath(".config/cyber-agent/api-token").read_text().strip(),"Content-Type":"application/json"})
 with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read())["choices"][0]["message"].get("content","")
rows=[]
for kind,p in CASES:
 row={"kind":kind,"prompt":p}
 for label,port in (("phase68",18766),("phase66",18767)):
  t=time.time()
  try: row[label]={"text":ask(port,p),"elapsed_s":round(time.time()-t,2)}
  except Exception as e: row[label]={"error":type(e).__name__,"elapsed_s":round(time.time()-t,2)}
 rows.append(row)
Path("phase68-quick-compare.json").write_text(json.dumps({"timeout_s":30,"cases":rows,"production_touched":False},ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"cases":len(rows),"report":"phase68-quick-compare.json"},ensure_ascii=False))
