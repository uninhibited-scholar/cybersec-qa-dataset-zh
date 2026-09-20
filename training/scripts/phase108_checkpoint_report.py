#!/usr/bin/env python3
"""Read-only validation/checkpoint inventory; never loads test scores or deploys."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re


VALIDATION = re.compile(r"Iter (\d+): Val loss ([^,\s]+)")
CHECKPOINT = re.compile(r"(\d+)_adapters\.safetensors")


def report(log: Path, directory: Path) -> dict:
    text = log.read_text(errors="replace")
    values = {}
    errors = []
    for match in VALIDATION.finditer(text):
        step = int(match[1])
        try:
            loss = float(match[2])
        except ValueError:
            errors.append(f"invalid_validation_at_step_{step}")
            continue
        if not math.isfinite(loss) or loss < 0:
            errors.append(f"invalid_validation_at_step_{step}")
            continue
        if step in values and values[step] != loss:
            errors.append(f"conflicting_validation_at_step_{step}")
        values[step] = loss
    candidates = []
    unmatched = []
    for path in sorted(directory.iterdir()):
        match = CHECKPOINT.fullmatch(path.name)
        if not match or not path.is_file():
            continue
        step = int(match[1])
        if path.stat().st_size == 0:
            errors.append(f"empty_checkpoint_at_step_{step}")
            continue
        if step not in values:
            unmatched.append(step)
            continue
        before = path.stat()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            errors.append(f"checkpoint_changed_during_read_at_step_{step}")
            continue
        candidates.append({"step": step, "pre_update_validation_loss": values[step],
                           "path": str(path), "sha256": digest})
    candidates.sort(key=lambda item: item["step"])
    return {
        "status": "invalid" if errors else "requires_common_validation" if candidates else "waiting_for_validated_checkpoint",
        "errors": errors,
        "validated_checkpoints": candidates,
        "checkpoint_steps_without_validation": unmatched,
        "suggested_for_behavior_evaluation": None,
        "production_approval": False,
        "limitations": ["Training-time validation draws new random batches; these losses cannot select a winner fairly.",
                        "MLX logs validation before the named iteration update but saves after it; logged loss is not a measurement of the saved checkpoint.",
                        "Reevaluate checkpoints on the same validation examples before selecting candidates; behavior evaluation remains required.",
                        "Unnumbered final weights are excluded because their step association is not established.",
                        "Run after training exits for a final inventory; a live run yields a provisional snapshot.",
                        "Test scores are not parsed or used for selection."],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    result = report(args.log, args.directory)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["errors"] else 0)
