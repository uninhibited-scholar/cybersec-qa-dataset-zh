#!/usr/bin/env python3
"""Metadata-only functional smoke for an isolated Phase108 loopback API.

This checks health, model discovery, one benign completion, and rejection of
tool requests. It never prints or stores prompt/response text. It is a serving
compatibility diagnostic, not a capability score or promotion gate.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request_json(url: str, payload: dict | None = None, timeout: int = 300):
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return response.status, json.loads(raw)
    except HTTPError as error:
        return error.code, json.loads(error.read())


def run(base_url: str, output: Path, scale: float) -> dict:
    started = time.monotonic()
    health_status, health = request_json(f"{base_url}/health", timeout=10)
    models_status, models = request_json(f"{base_url}/v1/models", timeout=10)
    chat_status, chat = request_json(
        f"{base_url}/v1/chat/completions",
        {
            "messages": [{"role": "user", "content": "请用一句话解释最小权限原则。"}],
            "max_tokens": 48,
            "temperature": 0.12,
            "top_p": 0.9,
            "tools": [],
        },
        timeout=300,
    )
    content = ""
    finish_reason = None
    if chat_status == 200:
        choices = chat.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content", "") if isinstance(message, dict) else ""
            finish_reason = choices[0].get("finish_reason")

    tool_status, _tool_error = request_json(
        f"{base_url}/v1/chat/completions",
        {
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1,
            "tools": [{"type": "function", "function": {"name": "forbidden"}}],
        },
        timeout=10,
    )
    model_ids = [row.get("id") for row in models.get("data", []) if isinstance(row, dict)]
    result = {
        "diagnostic": "loopback_api_function_smoke",
        "capability_score": False,
        "promotion_eligible": False,
        "scale": scale,
        "health_http": health_status,
        "health_ok": health_status == 200 and health.get("status") == "ok",
        "models_http": models_status,
        "model_ids": model_ids,
        "chat_http": chat_status,
        "chat_nonempty": bool(content.strip()),
        "response_chars": len(content),
        "finish_reason": finish_reason,
        "tool_request_http": tool_status,
        "tool_request_rejected": tool_status == 400,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scale", required=True, type=float)
    args = parser.parse_args()
    result = run(args.base_url.rstrip("/"), args.output, args.scale)
    if not result["health_ok"] or result["models_http"] != 200:
        raise SystemExit("API health/model discovery failed")


if __name__ == "__main__":
    main()
