import json
from pathlib import Path

p = Path(__file__).with_name("phase69_data.jsonl")
rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
assert len(rows) == 8
assert all(r["prompt"].strip() and r["completion"].strip() for r in rows)
assert not any("问题：" in r["completion"] or "回答：" in r["completion"] for r in rows)
assert not any(x in r["completion"].lower() for r in rows for x in ("rm -rf", "curl ", "nmap", "exploit"))
assert {r["source"] for r in rows} >= {"phase69-common-short", "phase69-common-free", "phase69-format-word", "phase69-format-json", "phase69-cyber-evidence", "phase69-cyber-defense"}
print({"rows": len(rows), "template_residue": 0, "operational_payloads": 0, "valid": True})
