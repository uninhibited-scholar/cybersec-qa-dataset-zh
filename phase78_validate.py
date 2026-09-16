import json
from pathlib import Path

rows=[json.loads(x) for x in Path(__file__).with_name("phase78_data.jsonl").read_text().splitlines() if x.strip()]
assert len(rows)==11
assert all(r["prompt"].strip() and r["completion"].strip() for r in rows)
assert not any(any(x in r["completion"] for x in ("问题：","回答：","---","```markdown")) for r in rows)
assert not any(x in r["completion"].lower() for r in rows for x in ("rm -rf","curl ","nmap","exploit","横向移动","数据窃取"))
assert {r["source"] for r in rows}=={"template-repair","defensive-answer","evidence-boundary","format","tool-boundary"}
print({"rows":11,"template_residue":0,"operational_payloads":0,"categories":5,"valid":True})
