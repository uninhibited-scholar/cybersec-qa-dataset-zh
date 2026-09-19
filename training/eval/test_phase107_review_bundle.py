import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from phase107_prepare_blind_review import build_bundle, validate_collection, write_private_jsonl


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
                "answer_keys_loaded": False, "protocol": "phase107-inference-protocol-v0.1",
                "max_tokens": 700, "temperature": 0.12, "top_p": 0.9,
                "repeat_penalty": 1.12, "repeat_context": 128,
                "tools": [], "client_retries": 0, "timeout_seconds": 300}
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


def test_private_jsonl_permissions(tmp_path):
    path = tmp_path / "private" / "bundle.jsonl"
    write_private_jsonl(path, [{"blind_alias": "A"}])
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
