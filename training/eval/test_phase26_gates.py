#!/usr/bin/env python3
"""Small stdlib-only regression suite for the Phase 26 safety gates."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))

from phase26_self_evolution_gate import evaluate  # noqa: E402
from candidate_manifest import build, verify  # noqa: E402


def record(i, *, known=False, generated=False, baseline=True, candidate=True, reward=0.7):
    return {
        "trajectory_id": f"t-{i}", "timestamp": "2026-09-28T00:00:00Z",
        "model_version": "candidate", "prompt": f"prompt-{i}",
        "response": "response", "source": "model_generated" if generated else "human_curated",
        "evaluator_version": "phase26-v1", "reward": reward, "tool_events": [],
        "known_prompt": known, "baseline_pass": baseline, "candidate_pass": candidate,
        "human_reviewed": not generated,
    }


def main():
    clean = evaluate([record(1, reward=.8), record(2, reward=.6)])
    assert clean["passed"]
    bad = evaluate([record(1, known=True, generated=True),
                    record(2, known=True, generated=True, candidate=False),
                    record(3, known=True, generated=True)])
    kinds = {item["kind"] for item in bad["failures"]}
    assert {"evaluation_deception", "capability_drift", "unreviewed_self_data"} <= kinds
    manifest = build(HERE / "fixtures", "fixture")
    assert verify(HERE / "fixtures", manifest) == []
    print("phase26 gates: PASS")


if __name__ == "__main__":
    main()
