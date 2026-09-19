import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_phase107_private_eval import to_messages


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
