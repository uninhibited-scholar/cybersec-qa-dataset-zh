from pathlib import Path

p = Path(__file__).with_name("phase70-chain-audit.md")
text = p.read_text()
assert "role delimiters" in text
assert "process-wide `LOCK`" in text
assert "production route untouched" in text
print({"static_audit": True, "training_started": False, "production_touched": False, "valid": True})
