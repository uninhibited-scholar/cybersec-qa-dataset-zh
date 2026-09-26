import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_phase108_private_source import CATEGORIES, build
from phase108_candidate_suite_preflight import preflight


def test_rejected_draft_exposes_reused_scenario_roots(tmp_path):
    rows = build()
    assert len(rows) == 320
    assert {row["category"] for row in rows} == set(CATEGORIES)
    assert len({row["fixture_id"] for row in rows}) == 320
    assert len({row["scenario_family"] for row in rows}) == 320
    assert len({row["scenario_root_id"] for row in rows}) == 40
    assert all(sum(other["scenario_root_id"] == row["scenario_root_id"] for other in rows) == 8
               for row in rows)
    assert all("Rejected draft" in row["independence_rationale"] for row in rows)
    assert all(len(row["prompt"]) > 50 for row in rows)

    source = tmp_path / "rejected-source.json"
    for row in rows:
        # The rejected draft's exact motif identity is repeated once per
        # category. Keep a unique category/fixture atom beside it so the new
        # atom-level gate specifically detects the shared incident fact.
        row["scenario_facts"] = [
            f"core incident {row['scenario_root_id']}",
            f"category-specific decision {row['category']} {row['fixture_id']}",
        ]
    source.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    report = preflight(source, expected_suite_version="phase108-v0.3")
    assert report["status"] == "fail"
    assert report["unique_scenario_roots"] == 40
    assert any("scenario_fact_reused_from_" in error for error in report["errors"])
    assert sum("duplicate_scenario_root_across_suite" in error for error in report["errors"]) == 280
