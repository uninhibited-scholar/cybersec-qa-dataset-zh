import json, time, urllib.request
from pathlib import Path
cases=[("ordinary","法国的首都是哪里？"),("cyber","请从防御角度说明 SSRF 的验证要点。"),("runtime","请说明本轮是否有真实工具回执。")]
rows=[]
for kind,p in cases:
 t=time.time(); body=json.dumps({"model":"qwen-cyber-agent","messages":[{"role":"system","content":"请保留此系统消息。"},{"role":"user","content":p}],"max_tokens":256}).encode(); req=urllib.request.Request("http://127.0.0.1:18768/v1/chat/completions",data=body,headers={"Authorization":"Bearer "+Path.home().joinpath(".config/cyber-agent/api-token").read_text().strip(),"Content-Type":"application/json"})
 try:
  with urllib.request.urlopen(req,timeout=30) as r:
   x=json.loads(r.read()); rows.append({"kind":kind,"text":x["choices"][0]["message"].get("content",""),"elapsed_s":round(time.time()-t,2)})
 except Exception as e: rows.append({"kind":kind,"error":type(e).__name__,"elapsed_s":round(time.time()-t,2)})
Path("phase71-regression.json").write_text(json.dumps({"phase":71,"results":rows,"production_touched":False},ensure_ascii=False,indent=2)+"\n")
print({"count":len(rows),"errors":sum("error" in r for r in rows)})
