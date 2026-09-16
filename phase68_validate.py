import json
from pathlib import Path

root = Path(__file__).resolve().parent
rows = [json.loads(line) for line in (root / "phase68_data.jsonl").read_text().splitlines() if line.strip()]
assert len(rows) == 6
assert all(isinstance(r.get("prompt"), str) and isinstance(r.get("completion"), str) and r["completion"].strip() for r in rows)
assert {r["source"] for r in rows} == {"phase68-neutral-short", "phase68-format-short", "phase68-evidence"}
assert sum(r["source"] == "phase68-evidence" for r in rows) == 3
assert not any("rm -rf" in r["completion"].lower() or "curl " in r["completion"].lower() for r in rows)
print({"rows": len(rows), "evidence_rows": 3, "neutral_rows": 3, "payloads": 0, "valid": True})
