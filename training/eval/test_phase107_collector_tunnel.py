import pytest

from phase107_collect_blind import (
    EXPECTED_PHASE91_WORKER_SHA256,
    EXPECTED_SYSTEM_PROMPT_SHA256,
    cluster_tunnel_command,
    read_jsonl,
    validate_reference_local_resume,
)


def test_cluster_forward_targets_compute_node_loopback_services():
    command = cluster_tunnel_command("zj225", "slurmc.ie.cuhk.edu.hk", "a100-3")
    assert command[:5] == ["ssh", "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes"]
    assert "127.0.0.1:18181:a100-3:18081" in command
    assert "127.0.0.1:18182:a100-3:18082" in command
    assert command[-1] == "zj225@slurmc.ie.cuhk.edu.hk"


def test_cluster_forward_ports_can_be_overridden_without_shell_interpolation():
    command = cluster_tunnel_command("zj225", "slurmc.ie.cuhk.edu.hk", "a100-3", 18181, 18182)
    assert "127.0.0.1:18181:a100-3:18181" in command
    assert "127.0.0.1:18182:a100-3:18182" in command
    assert all(";" not in part for part in command)


def test_reference_local_resume_requires_the_complete_prior_phase91_arm():
    cases = [{"id": f"case-{i}"} for i in range(320)]
    aliases = {"A": "phase91", "B": "gptoss20b", "C": "gemma4_26b"}
    prior = {
        "suite_version": "phase107-v0.2",
        "case_count": 320,
        "suite_sha256": "suite-hash",
        "answer_keys_loaded": False,
        "protocol": "phase107-inference-protocol-v0.1+corrigendum-v0.1.1",
        "phase91_prompt_parity": {
            "worker_sha256": EXPECTED_PHASE91_WORKER_SHA256,
            "system_prompt_sha256": EXPECTED_SYSTEM_PROMPT_SHA256,
        },
    }
    completed = {(case["id"], "A") for case in cases}
    assert validate_reference_local_resume(cases, completed, aliases, prior, "suite-hash") == prior["phase91_prompt_parity"]
    with pytest.raises(ValueError, match="missing=1"):
        validate_reference_local_resume(cases, completed - {("case-0", "A")}, aliases, prior, "suite-hash")


def test_reference_local_resume_rejects_prompt_or_suite_drift():
    cases = [{"id": f"case-{i}"} for i in range(320)]
    aliases = {"A": "phase91", "B": "gptoss20b", "C": "gemma4_26b"}
    completed = {(case["id"], "A") for case in cases}
    prior = {
        "suite_version": "phase107-v0.2", "case_count": 320, "suite_sha256": "wrong",
        "answer_keys_loaded": False,
        "protocol": "phase107-inference-protocol-v0.1+corrigendum-v0.1.1",
        "phase91_prompt_parity": {
            "worker_sha256": EXPECTED_PHASE91_WORKER_SHA256,
            "system_prompt_sha256": EXPECTED_SYSTEM_PROMPT_SHA256,
        },
    }
    with pytest.raises(ValueError, match="manifest"):
        validate_reference_local_resume(cases, completed, aliases, prior, "expected")


def test_read_jsonl_accepts_objects_and_rejects_bad_rows(tmp_path):
    path = tmp_path / "rows.jsonl"
    path.write_text('{"id":"one"}\n\n{"id":"two"}\n', encoding="utf-8")
    assert read_jsonl(path) == [{"id": "one"}, {"id": "two"}]
    path.write_text("[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="non-object"):
        read_jsonl(path)
