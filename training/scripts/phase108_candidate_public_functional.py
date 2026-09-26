#!/usr/bin/env python3
"""Metadata-only public functional diagnostic for an isolated Phase108 API.

This is a compatibility/empty-output screen, not a capability score. Prompts
are fixed, benign development probes. Neither prompts nor generated text are
written to the result file or printed.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


PROBES = (
    ("general_overfit", "用一句话解释机器学习中的过拟合。"),
    ("general_json", "用 JSON 表示一个名为 status、值为 ok 的对象，只输出 JSON。"),
    ("general_uncertainty", "如果现有信息不足以判断，请用一句话说明还缺什么信息。"),
    ("defensive_concept", "用一句话说明为什么软件应只授予完成任务所需的最小权限。"),
)


def request_json(url: str, payload: dict | None = None, timeout: int = 300):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        try:
            json.loads(error.read())
        except Exception:
            pass
        return error.code, {}


def run(base_url: str, output: Path, scale: float, adapter_sha256: str) -> dict:
    started = time.monotonic()
    health_status, health = request_json(f"{base_url}/health", timeout=10)
    models_status, _models = request_json(f"{base_url}/v1/models", timeout=10)
    rows = []
    for probe_id, prompt in PROBES:
        status, body = request_json(
            f"{base_url}/v1/chat/completions",
            {"messages": [{"role": "user", "content": prompt}],
             "max_tokens": 64, "temperature": 0.0, "tools": []},
            timeout=300,
        )
        content, finish = "", None
        choices = body.get("choices") if isinstance(body, dict) else None
        if status == 200 and isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content", "") if isinstance(message, dict) else ""
            finish = choices[0].get("finish_reason")
        rows.append({"probe_id": probe_id, "http": status,
                     "nonempty": bool(content.strip()), "chars": len(content),
                     "finish_reason": finish})

    tool_status, _ = request_json(
        f"{base_url}/v1/chat/completions",
        {"messages": [{"role": "user", "content": "test"}], "max_tokens": 1,
         "tools": [{"type": "function", "function": {"name": "forbidden"}}]},
        timeout=10,
    )
    result = {
        "diagnostic": "phase108_public_functional_empty_output_screen",
        "capability_score": False,
        "blind_evaluation": False,
        "promotion_eligible": False,
        "scale": scale,
        "adapter_sha256": adapter_sha256,
        "health_http": health_status,
        "health_ok": health_status == 200 and health.get("status") == "ok",
        "models_http": models_status,
        "probes": rows,
        "nonempty_count": sum(row["nonempty"] for row in rows),
        "empty_count": sum(not row["nonempty"] for row in rows),
        "http_error_count": sum(row["http"] != 200 for row in rows),
        "tool_request_http": tool_status,
        "tool_request_rejected": tool_status == 400,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    output.write_text(json.dumps(result, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scale", required=True, type=float)
    parser.add_argument("--adapter-sha256", required=True)
    args = parser.parse_args()
    result = run(args.base_url.rstrip("/"), args.output, args.scale, args.adapter_sha256)
    if not result["health_ok"] or result["models_http"] != 200:
        raise SystemExit("candidate API health/model discovery failed")


if __name__ == "__main__":
    main()
