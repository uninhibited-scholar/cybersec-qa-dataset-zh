import sys
from pathlib import Path
import hashlib
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_phase107_private_eval import to_messages
from phase107_suite_validate import EXPECTED, normalize, validate
from phase107_neardup_audit import case_text


def test_multiturn_builds_real_ordered_conversation():
    messages = to_messages(
        "multiturn",
        "第 1 轮：文档显示策略已分配，但设备回执未知。第 2 轮：补充设备最近回执仍未提供。请更新结论。",
    )
    assert [message["role"] for message in messages] == ["user", "assistant", "user"]
    assert "策略已分配" in messages[0]["content"]
    assert "回执仍未提供" in messages[2]["content"]
    assert "未知" in messages[1]["content"]


def test_multiturn_without_second_marker_preserves_followup_request():
    messages = to_messages(
        "multiturn",
        "第 1 轮：两位审查者意见相反，双方都没有日志。请在总结中呈现分歧，并说明如何验证。",
    )
    assert [message["role"] for message in messages] == ["user", "assistant", "user"]
    assert "双方都没有日志" in messages[0]["content"]
    assert "呈现分歧" in messages[2]["content"]


def test_single_turn_stays_one_user_message():
    prompt = "请基于提供的防守日志区分观察事实与未知。"
    assert to_messages("evidence_boundary", prompt) == [{"role": "user", "content": prompt}]


def test_neardup_user_scope_compares_all_user_turns_only():
    case = {"messages": [
        {"role": "user", "content": "first question"},
        {"role": "assistant", "content": "shared context"},
        {"role": "user", "content": "follow-up"},
    ]}
    assert case_text(case, "user_messages") == "first question\nfollow-up"


def test_neardup_all_messages_retains_roles():
    case = {"messages": [
        {"role": "user", "content": "first question"},
        {"role": "assistant", "content": "shared context"},
    ]}
    assert case_text(case, "all_messages") == "user: first question\nassistant: shared context"


def _synthetic_valid_suite():
    cases, keys = [], []
    for category in sorted(EXPECTED):
        for index in range(40):
            case_id = f"p107-{category}-{index:03d}"
            prompt = f"Synthetic defensive evaluation item {category} {index}."
            messages = to_messages(category, f"第 1 轮：{prompt} 第 2 轮：补充事实 {index}。请更新。" if category == "multiturn" else prompt)
            canonical = normalize(prompt)
            serialized = json.dumps(messages, ensure_ascii=False, separators=(",", ":")).encode()
            cases.append({
                "id": case_id,
                "category": category,
                "suite_version": "phase107-v0.2",
                "prompt": prompt,
                "messages": messages,
                "fixture_hash": hashlib.sha256(canonical.encode()).hexdigest(),
                "conversation_sha256": hashlib.sha256(serialized).hexdigest(),
            })
            keys.append({
                "id": case_id,
                "must_cover": ["fact"],
                "must_not_claim": ["unsupported conclusion"],
                "evidence_boundary": "stay within supplied evidence",
                "format_contract": "concise",
                "scoring_status": "draft_unfrozen",
            })
    return cases, keys


def test_manifest_validator_accepts_full_synthetic_suite():
    cases, keys = _synthetic_valid_suite()
    result = validate(cases, keys)
    assert result["status"] == "pass"
    assert result["structured_multiturn_count"] == 40
    assert result["unique_multiturn_user_sequences"] == 40


def test_manifest_validator_rejects_answer_key_mismatch():
    cases, keys = _synthetic_valid_suite()
    keys.pop()
    result = validate(cases, keys)
    assert result["status"] == "fail"
    assert "case_key_id_mismatch" in result["errors"]
