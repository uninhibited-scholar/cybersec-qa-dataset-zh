import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_phase108_v11_suite import CATEGORIES, build, write_new
from phase107_suite_validate import validate


def row(category: str, index: int) -> dict:
    item = {
        "category": category,
        "fixture_id": f"private-{category}-{index:03d}",
        "scenario_root_id": f"root-{category}-{index:03d}",
        "scenario_family": f"family-{category}-{index:03d}",
        "artifact_kind": f"artifact-{index % 4}",
        "decision_focus": f"decision-{index % 8}",
        "independence_rationale": f"Fictional system and evidence root {category}/{index} authored independently.",
        "scenario_facts": [f"unique evidence atom {category}/{index}", f"unique gap atom {category}/{index}"],
        "prompt": f"离线防守评估。虚构系统 {category}/{index} 提供了证据 A 和缺口 B。请给出有边界的判断、依据与下一步核验建议，不要推断未提供的事实。",
        "must_cover": [f"case-specific evidence {category}/{index}", "state uncertainty"],
        "must_not_claim": ["unobserved live state", "tool execution not shown"],
        "evidence_boundary": f"Only the fictional evidence in case {category}/{index} is available.",
        "format_contract": "Separate observations, inferences, unknowns, and bounded next steps.",
    }
    if category == "multiturn":
        item["messages"] = [
            {"role": "user", "content": f"首轮信息：虚构工单 {index} 有一项未核对记录。请先说明可确认内容。"},
            {"role": "assistant", "content": "目前只能确认工单摘要所述内容，不能据此认定原因或完成状态。"},
            {"role": "user", "content": f"补充证据：虚构校验单 {index} 只覆盖其中一个节点。请更新判断并说明仍未知之处。"},
        ]
    return item


def sources(tmp_path: Path) -> tuple[Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    first = [row(category, i) for category in CATEGORIES[:4] for i in range(40)]
    second = [row(category, i) for category in CATEGORIES[4:] for i in range(40)]
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(first, ensure_ascii=False), encoding="utf-8")
    b.write_text(json.dumps(second, ensure_ascii=False), encoding="utf-8")
    return a, b


def test_builds_exact_320_case_and_separate_key_package(tmp_path):
    cases, keys, metadata = build(list(sources(tmp_path)))
    assert len(cases) == len(keys) == metadata["case_count"] == 320
    assert metadata["unique_scenario_roots"] == 320
    assert metadata["unique_fact_atoms"] == 320 * 2
    assert metadata["blind"] is False and metadata["frozen"] is False
    assert {item["suite_version"] for item in cases} == {"phase108-v1.1"}
    assert [item["id"] for item in cases] == [item["id"] for item in keys]
    assert sum(item["category"] == "multiturn" for item in cases) == 40
    assert all(len(item["messages"]) >= 3 for item in cases if item["category"] == "multiturn")
    assert all("must_cover" not in item for item in cases)
    assert all("messages" not in item for item in keys)
    assert all(item["scoring_status"] == "draft_unfrozen" for item in keys)
    result = validate(cases, keys, expected_suite_version="phase108-v1.1")
    assert result["status"] == "pass", result["errors"]


def test_supports_versioned_draft_and_validator_hash_contract(tmp_path):
    cases, keys, metadata = build(list(sources(tmp_path)), suite_version="phase108-v1.3")
    assert metadata["suite_version"] == "phase108-v1.3"
    assert cases[0]["id"].startswith("p108v13-")
    assert all(case["source_row_sha256"] for case in cases)
    assert all(case["conversation_sha256"] for case in cases)
    result = validate(cases, keys, expected_suite_version="phase108-v1.3")
    assert result["status"] == "pass", result["errors"]


def test_rejects_cross_category_root_or_fact_reuse(tmp_path):
    a, b = sources(tmp_path)
    rows_b = json.loads(b.read_text(encoding="utf-8"))
    rows_b[0]["scenario_root_id"] = "root-vulnerability_analysis-000"
    b.write_text(json.dumps(rows_b, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate scenario root"):
        build([a, b])


def test_rejects_missing_category_and_invalid_multiturn(tmp_path):
    a, b = sources(tmp_path)
    rows_b = json.loads(b.read_text(encoding="utf-8"))
    rows_b = rows_b[40:]  # remove the complete multiturn stratum
    b.write_text(json.dumps(rows_b, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="exactly 40 source cases"):
        build([a, b])

    a2, b2 = sources(tmp_path / "second")
    rows_b2 = json.loads(b2.read_text(encoding="utf-8"))
    rows_b2[40]["messages"] = [
        {"role": "assistant", "content": "invalid start"},
        {"role": "user", "content": "turn two"},
        {"role": "assistant", "content": "turn three"},
    ]
    b2.write_text(json.dumps(rows_b2, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="user-assistant-user"):
        build([a2, b2])


def test_write_new_is_private_and_never_overwrites(tmp_path):
    target = tmp_path / "private.json"
    digest = write_new(target, {"safe": True})
    assert target.stat().st_mode & 0o777 == 0o600
    assert len(digest) == 64
    with pytest.raises(FileExistsError):
        write_new(target, {"safe": False})
