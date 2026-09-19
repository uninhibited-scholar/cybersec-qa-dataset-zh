import ast
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase107_collect_blind as collector


WORKER_FIXTURE = b'''\
def render_prompt(messages, tools):
    system_parts = ["base system"]
    if tools:
        system_parts.append("tool inventory")
    else:
        system_parts.append("no tools")
    return "\\n".join(system_parts)
'''


def test_extracts_effective_no_tool_system_without_executing_worker():
    assert collector.extract_no_tool_system(WORKER_FIXTURE) == "base system\nno tools"


def test_rejects_prompt_mismatch_before_inference(monkeypatch):
    monkeypatch.setattr(collector, "EXPECTED_PHASE91_WORKER_SHA256", collector.sha256_bytes(WORKER_FIXTURE))
    monkeypatch.setattr(collector, "EXPECTED_SYSTEM_PROMPT_SHA256", collector.sha256_bytes(b"reference system"))
    with pytest.raises(ValueError, match="differs from reference"):
        collector.validate_prompt_parity(WORKER_FIXTURE, "reference system")


def test_reference_prompt_hash_is_pinned_to_frozen_protocol_copy():
    source = Path(__file__).with_name("phase107_collect_blind.py").read_bytes()
    tree = ast.parse(source)
    system_prompt = next(
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "SYSTEM_PROMPT"
    )
    assert collector.sha256_bytes(system_prompt.encode("utf-8")) == collector.EXPECTED_SYSTEM_PROMPT_SHA256
