#!/usr/bin/env python3
"""Authenticated, non-destructive smoke test for the local OpenAI-style API."""
import json
import os
import sys
import urllib.request


BASE = os.environ.get("CYBER_API_URL", "http://127.0.0.1:18765").rstrip("/")
TOKEN = os.environ.get("CYBER_API_TOKEN", "")


def request(path, payload=None):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(BASE + path, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.status, json.loads(response.read().decode())


def main():
    status, health = request("/health")
    result = {"health_status": status, "health": health, "token_supplied": bool(TOKEN)}
    if TOKEN:
        status, body = request("/v1/chat/completions", {
            "model": "qwen-cyber-local",
            "stream": False,
            "max_tokens": 80,
            "messages": [{"role": "user", "content": "用一句话解释缓存是什么。"}],
        })
        answer = body.get("choices", [{}])[0].get("message", {}).get("content", "")
        result.update({"completion_status": status, "model": body.get("model"),
                       "answer_nonempty": bool(answer.strip())})
    else:
        result["note"] = "未提供令牌；跳过生成请求，令牌不会被猜测或打印。"
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"passed": False, "error_type": type(exc).__name__}, ensure_ascii=False))
        sys.exit(1)
