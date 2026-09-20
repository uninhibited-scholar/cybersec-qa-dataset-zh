import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from phase107_collect_blind import (
    run_case_request,
    submit_parallel_reference_requests,
)


def test_parallel_reference_requests_start_in_given_randomized_order_and_overlap():
    started = []
    active = set()
    max_active = 0
    lock = threading.Lock()

    def fake_request(system, case, arm_order, aliases, endpoints, started_event):
        nonlocal max_active
        with lock:
            started.append(system)
            active.add(system)
            max_active = max(max_active, len(active))
        started_event.set()
        time.sleep(0.05)
        with lock:
            active.remove(system)
        return {"system": system}

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = submit_parallel_reference_requests(
            executor, ["gemma4_26b", "gptoss20b"], {}, [], {}, {}, fake_request)
        results = [future.result() for future in as_completed(futures)]

    assert started == ["gemma4_26b", "gptoss20b"]
    assert max_active == 2
    assert {row["system"] for row in results} == {"gptoss20b", "gemma4_26b"}


def test_run_case_request_preserves_protocol_payload(monkeypatch):
    captured = {}

    def fake_completion(url, payload, token, started_event=None):
        captured.update(url=url, payload=payload, token=token)
        return {"content": "ok", "classification": "ok", "transport_status": 200,
                "finish_reason": "stop", "first_content_s": 0.1, "total_s": 0.2}

    monkeypatch.setattr("phase107_collect_blind.stream_completion", fake_completion)
    case = {"id": "case-x", "category": "defensive", "messages": [{"role": "user", "content": "test"}]}
    aliases = {"phase91": "A", "gptoss20b": "B", "gemma4_26b": "C"}
    row = run_case_request("gptoss20b", case, ["gptoss20b", "gemma4_26b"], aliases,
                           {"gptoss20b": ("http://127.0.0.1:18081/v1/chat/completions", None)})

    assert captured["url"].endswith("/v1/chat/completions")
    assert captured["payload"]["messages"] == [
        {"role": "system", "content": __import__("phase107_collect_blind").SYSTEM_PROMPT},
        {"role": "user", "content": "test"},
    ]
    assert captured["payload"]["tools"] == []
    assert captured["payload"]["max_tokens"] == 700
    assert captured["payload"]["temperature"] == 0.12
    assert captured["payload"]["top_p"] == 0.9
    assert row["alias"] == "B"
    assert row["arm_order_for_case"] == ["B", "C"]
