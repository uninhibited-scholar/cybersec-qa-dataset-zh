#!/usr/bin/env python3
"""Metadata-only smoke checks for the isolated dual-model API service.

Response text is inspected in memory to establish non-empty output, but never
printed or persisted. This proves serving compatibility only, not model
quality or cybersecurity capability.
"""
from __future__ import annotations

import argparse
import json
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def get_json(url: str, timeout: int = 10) -> tuple[int, dict, str | None]:
    request = Request(url)
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read()), response.headers.get("X-Model-Route")
    except HTTPError as error:
        return error.code, json.loads(error.read()), error.headers.get("X-Model-Route")


def chat(base: str, stream: bool, timeout: int = 300) -> dict:
    payload = {
        "model": "qwen3-14b-bf16",
        "messages": [{"role": "user", "content": "Reply with one short sentence confirming this endpoint is responding."}],
        "max_tokens": 32,
        "temperature": 0,
        "stream": stream,
    }
    request = Request(
        base + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.monotonic()
    with urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", "replace")
        route = response.headers.get("X-Model-Route")
        status = response.status
        content_type = response.headers.get("Content-Type", "")

    pieces: list[str] = []
    done = False
    if stream:
        for line in body.splitlines():
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                done = True
                continue
            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                continue
            choices = event.get("choices")
            if isinstance(choices, list) and choices:
                delta = choices[0].get("delta", {})
                if isinstance(delta, dict) and isinstance(delta.get("content"), str):
                    pieces.append(delta["content"])
    else:
        parsed = json.loads(body)
        choices = parsed.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                pieces.append(message["content"])

    text = "".join(pieces).strip()
    return {
        "http": status,
        "route": route,
        "stream": stream,
        "sse_content_type": "text/event-stream" in content_type.lower() if stream else None,
        "sse_done": done if stream else None,
        "nonempty": bool(text),
        "response_chars": len(text),
        "reasoning_marker": "<think>" in text or "</think>" in text,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-route", choices=("big", "small_fallback"), required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    health_status, health, _ = get_json(base + "/health")
    models_status, models, _ = get_json(base + "/v1/models")
    nonstream = chat(base, stream=False)
    stream = chat(base, stream=True)
    model_ids = [row.get("id") for row in models.get("data", []) if isinstance(row, dict)]
    result = {
        "diagnostic": "dual_model_api_service_smoke",
        "capability_score": False,
        "promotion_eligible": False,
        "expected_route": args.expected_route,
        "health_http": health_status,
        "health": health,
        "models_http": models_status,
        "model_ids": model_ids,
        "nonstream": nonstream,
        "stream": stream,
    }
    with open(args.output, "w", encoding="utf-8") as output:
        json.dump(result, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)

    if health_status != 200 or health.get("status") != "ok":
        raise SystemExit("API health check failed")
    if models_status != 200 or "qwen3-14b-bf16" not in model_ids:
        raise SystemExit("API model discovery failed")
    for response in (nonstream, stream):
        if response["http"] != 200 or response["route"] != args.expected_route or not response["nonempty"]:
            raise SystemExit("API chat route or response check failed")
        if response["reasoning_marker"]:
            raise SystemExit("reasoning-channel marker leaked")
    if not stream["sse_content_type"] or not stream["sse_done"]:
        raise SystemExit("SSE framing check failed")


if __name__ == "__main__":
    main()
