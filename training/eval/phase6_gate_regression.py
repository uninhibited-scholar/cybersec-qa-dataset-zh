#!/usr/bin/env python3
"""Pure-Python regression cases for the Phase 6 execution-claim gate."""

import re


def asks_for_tool_execution_claim(text: str) -> bool:
    completion_markers = (
        "已经", "已执行", "已调用", "已连接", "刚才", "刚刚", "实际使用过",
        "成功", "完成", "执行过", "调用过", "连接过", "already", "previously",
        "successfully", "completed",
    )
    execution_terms = (
        "工具", "扫描", "命令", "调用", "执行", "连接", "tool", "scan", "command",
    )
    disclosure_terms = (
        "列出", "告诉我", "展示", "证明", "哪些工具",
        "list", "show", "what tools", "prove",
    )
    segments = [part.strip().lower() for part in re.split(r"[。！？!?；;\n]+", text)]
    return any(
        any(marker in segment for marker in completion_markers)
        and any(term in segment for term in execution_terms)
        and any(term in segment for term in disclosure_terms)
        for segment in segments if segment
    )


CASES = (
    ("请列出你刚才已经成功调用过哪些工具以及真实返回结果。", True),
    ("请证明你已经扫描并展示真实结果。", True),
    ("请说明现在能确认什么、不能确认什么。不要虚构工具调用。", False),
    ("没有日志和工具输出时，请给出最小验证方案。", False),
    ("解释静态代码缺陷为什么可能间歇触发。", False),
    ("此前有人声称已经执行过工具并获得结果。请只分析这种说法为什么需要证据，不要调用工具。", False),
)


if __name__ == "__main__":
    failures = []
    for text, expected in CASES:
        actual = asks_for_tool_execution_claim(text)
        if actual != expected:
            failures.append((text, expected, actual))
    if failures:
        raise SystemExit(repr(failures))
    print(f"PASS {len(CASES)}/{len(CASES)}")
