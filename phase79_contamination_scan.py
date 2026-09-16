import json, re
from pathlib import Path

roots=[Path.home()/"datasets/cybersec-phase78",Path.home()/"datasets/cybersec-phase69",Path.home()/"datasets/cybersec-phase68"]
markers=re.compile(r"银行|内部网关|93\.176\.120\.112|2024-03-15|User login successful|admin",re.I)
hits=[]; files=0
for root in roots:
 for p in root.glob("*.jsonl"):
  files+=1
  for n,line in enumerate(p.read_text(errors="ignore").splitlines(),1):
   if markers.search(line): hits.append({"file":str(p),"line":n})
out={"phase":79,"scanned_files":files,"training_set_hits":hits,"training_set_clean":not hits,"candidate_output_contamination":"observed_in_phase78_regression","recommendation":"keep contaminated traces out of training; add canary prompt and reject output containing known private/project literals","production_touched":False}
Path("phase79-contamination-scan.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print({"scanned_files":files,"hits":len(hits),"clean":not hits})
