import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from phase108_candidate_suite_preflight import EXPECTED, preflight


def fixture(category, index):
    return {
        "category": category,
        "fixture_id": f"fresh-{category}-{index}",
        "prompt": f"独立防守评测 {category} 场景 {index}，请基于给定材料区分事实、推断和未知。",
        "scenario_root_id": f"scenario-root-{category}-{index}",
        "must_cover": ["evidence"], "must_not_claim": ["unsupported"],
        "evidence_boundary": "Only supplied material is evidence.",
        "format_contract": "Label observations, inferences, and unknowns.",
        "scenario_family": f"family-{index % 20}",
        "artifact_kind": f"artifact-{index % 4}",
        "decision_focus": f"decision-{index % 8}",
        "independence_rationale": "New offline synthetic fixture, separately authored for candidate evaluation.",
    }


def full_source():
    return [fixture(category, index) for category in sorted(EXPECTED) for index in range(40)]


def test_preflight_accepts_structurally_diverse_full_source(tmp_path):
    path = tmp_path / "source.json"
    path.write_text(json.dumps(full_source(), ensure_ascii=False))
    result = preflight(path, expected_suite_version="phase108-v0.3")
    assert result["status"] == "pass"
    assert result["case_count"] == 320
    assert result["private_text_printed"] is False


def test_preflight_rejects_repeated_scenario_triplet(tmp_path):
    rows = full_source()
    rows[1]["scenario_family"] = rows[0]["scenario_family"]
    rows[1]["artifact_kind"] = rows[0]["artifact_kind"]
    rows[1]["decision_focus"] = rows[0]["decision_focus"]
    path = tmp_path / "source.json"
    path.write_text(json.dumps(rows, ensure_ascii=False))
    result = preflight(path, expected_suite_version="phase108-v0.3")
    assert result["status"] == "fail"
    assert any("duplicate_scenario_artifact_decision" in error for error in result["errors"])


def test_preflight_rejects_same_scenario_root_across_categories(tmp_path):
    rows = full_source()
    rows[40]["scenario_root_id"] = rows[0]["scenario_root_id"]
    path = tmp_path / "source.json"
    path.write_text(json.dumps(rows, ensure_ascii=False))
    result = preflight(path, expected_suite_version="phase108-v1.0")
    assert result["status"] == "fail"
    assert any("duplicate_scenario_root_across_suite" in error for error in result["errors"])
    assert result["unique_scenario_roots"] == 319


def test_preflight_rejects_missing_scenario_root_id(tmp_path):
    rows = full_source()
    del rows[0]["scenario_root_id"]
    path = tmp_path / "source.json"
    path.write_text(json.dumps(rows, ensure_ascii=False))
    result = preflight(path, expected_suite_version="phase108-v1.0")
    assert result["status"] == "fail"
    assert any("missing_scenario_root_id" in error for error in result["errors"])


def test_preflight_rejects_missing_format_contract(tmp_path):
    rows = full_source()
    del rows[0]["format_contract"]
    path = tmp_path / "source.json"
    path.write_text(json.dumps(rows, ensure_ascii=False))
    result = preflight(path, expected_suite_version="phase108-v1.0")
    assert result["status"] == "fail"
    assert any("missing_format_contract" in error for error in result["errors"])


@pytest.mark.parametrize("field", ["must_cover", "must_not_claim"])
def test_preflight_rejects_nontext_answer_key_entries(tmp_path, field):
    rows = full_source()
    rows[0][field] = ["valid item", " "]
    path = tmp_path / "source.json"
    path.write_text(json.dumps(rows, ensure_ascii=False))
    result = preflight(path, expected_suite_version="phase108-v1.0")
    assert result["status"] == "fail"
    assert any(f"invalid_{field}" in error for error in result["errors"])
