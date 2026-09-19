import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from phase107_prepare_blind_review import (
    CALIBRATION_RULES,
    build_bundle,
    validate_collection,
    write_private_jsonl,
)


def sample_data():
    cases = [
        {"id": f"case-{i}", "category": f"cat-{i % 8}", "messages": [{"role": "user", "content": f"Q{i}"}]}
        for i in range(320)
    ]
    keys = [
        {"id": c["id"], "must_cover": ["fact"], "must_not_claim": ["unknown"],
         "evidence_boundary": "provided evidence", "format_contract": "concise"}
        for c in cases
    ]
    responses = [
        {"case_id": c["id"], "category": c["category"], "alias": alias, "content": f"A-{alias}-{c['id']}",
         "classification": "ok", "finish_reason": "stop", "transport_status": 200,
         "first_content_s": 0.1, "total_s": 0.2, "arm_order_for_case": ["A", "B", "C"]}
        for c in cases for alias in ("A", "B", "C")
    ]
    manifest = {"suite_version": "phase107-v0.2", "case_count": 320,
                "answer_keys_loaded": False,
                "protocol": "phase107-inference-protocol-v0.1+corrigendum-v0.1.1",
                "max_tokens": 700, "temperature": 0.12, "top_p": 0.9,
                "repeat_penalty": 1.12, "repeat_context": 128,
                "tools": [], "client_retries": 0, "timeout_seconds": 300}
    manifest["phase91_prompt_parity"] = {
        "worker_sha256": "a4936301d54bb08bf8b7fa82847e090bbba827c6815513dd5d2d3ae88f7302cb",
        "system_prompt_sha256": "6017e9aab198e717f3d61082e08e45ca6fd0afa2158f750c43e1966110efe57e",
    }
    return cases, keys, responses, manifest


def test_collection_requires_complete_unique_three_arm_coverage():
    cases, _, responses, manifest = sample_data()
    case_ids, aliases = validate_collection(cases, responses, manifest)
    assert len(case_ids) == 320
    assert aliases == {"A", "B", "C"}
    with pytest.raises(ValueError, match="incomplete"):
        validate_collection(cases, responses[:-1], manifest)
    changed = dict(manifest, tools=[{"type": "function"}])
    with pytest.raises(ValueError, match="frozen Phase 107"):
        validate_collection(cases, responses, changed)
    prompt_mismatch = dict(manifest, phase91_prompt_parity={
        "worker_sha256": "a4936301d54bb08bf8b7fa82847e090bbba827c6815513dd5d2d3ae88f7302cb",
        "system_prompt_sha256": "wrong",
    })
    with pytest.raises(ValueError, match="corrigendum hash"):
        validate_collection(cases, responses, prompt_mismatch)


def test_bundle_hides_arm_order_and_only_keeps_blind_aliases():
    cases, keys, responses, _ = sample_data()
    bundle = build_bundle(cases, keys, responses, seed=17)
    assert len(bundle) == 320
    assert len(bundle[0]["responses"]) == 3
    assert set(bundle[0]["responses"][0]) == {
        "blind_alias", "content", "classification", "finish_reason", "transport_status",
        "first_content_s", "total_s",
    }
    assert "arm_order_for_case" not in bundle[0]["responses"][0]
    assert "model_name" not in bundle[0]["responses"][0]


def test_calibration_annotations_are_applied_without_changing_keys():
    cases, keys, responses, _ = sample_data()
    special_ids = [
        "p107-prompt_injection-024",
        "p107-prompt_injection-028",
        "p107-multiturn-021",
        "p107-multiturn-035",
    ]
    for index, case_id in enumerate(special_ids):
        cases[index]["id"] = case_id
        keys[index]["id"] = case_id
        for row in responses[index * 3:(index + 1) * 3]:
            row["case_id"] = case_id
    original_key = {k: v for k, v in keys[0].items() if k != "id"}
    bundle = build_bundle(cases, keys, responses, seed=17)
    by_id = {item["case_id"]: item for item in bundle}

    pi24 = by_id["p107-prompt_injection-024"]["calibration_adjudication"]
    assert pi24["status"] == "exclude_case_from_aggregate"
    assert pi24["quality_scoring"] is False
    assert pi24["model_failure_counting"] is False
    assert {k: v for k, v in by_id["p107-prompt_injection-024"]["answer_key"].items()} == original_key

    pi28 = by_id["p107-prompt_injection-028"]["calibration_adjudication"]
    assert pi28["status"] == "conditional_scorability"
    assert pi28["quality_scoring"] == "only_if_resolvable_without_assumptions"
    for case_id in special_ids[2:]:
        note = by_id[case_id]["calibration_adjudication"]
        assert note["status"] == "score_against_actual_transcript"
        assert "Do not require retracting" in note["note"]


def test_calibration_rules_require_quote_and_blind_adjudication():
    assert any("short supporting answer quote" in rule for rule in CALIBRATION_RULES)
    assert any("identities remain blind" in rule for rule in CALIBRATION_RULES)
    assert any("double-penalize" in rule for rule in CALIBRATION_RULES)


def test_private_jsonl_permissions(tmp_path):
    path = tmp_path / "private" / "bundle.jsonl"
    write_private_jsonl(path, [{"blind_alias": "A"}])
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
