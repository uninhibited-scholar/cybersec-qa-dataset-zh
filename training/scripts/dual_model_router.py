#!/usr/bin/env python3
"""OpenAI-compatible router with a large-model default and CPU fallback.

The router never claims the fallback is the large model.  It adds an
X-Model-Route response header and a route field in /health.  Backends are
configured by environment variables so production services are untouched.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BIG = os.environ.get("BIG_API", "http://127.0.0.1:19000").rstrip("/")
SMALL = os.environ.get("SMALL_API", "http://127.0.0.1:19001").rstrip("/")
PORT = int(os.environ.get("ROUTER_PORT", "19002"))
TIMEOUT = float(os.environ.get("BIG_TIMEOUT_SECONDS", "8"))
PUBLIC_MODEL_ID = os.environ.get("PUBLIC_MODEL_ID", "qwen3-14b-bf16")


def health(url: str) -> bool:
    try:
        with urllib.request.urlopen(url + "/health", timeout=1.5) as response:
            return 200 <= response.status < 300
    except (OSError, urllib.error.URLError):
        return False


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, status: int, body: bytes, route: str = "router") -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Model-Route", route)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            big_ok, small_ok = health(BIG), health(SMALL)
            body = json.dumps({"status": "ok" if big_ok or small_ok else "unavailable", "big": big_ok, "small": small_ok}).encode()
            self._send(200, body)
            return
        if self.path == "/v1/models":
            body = json.dumps({"object": "list", "data": [{"id": PUBLIC_MODEL_ID, "object": "model", "owned_by": "local-router"}]}).encode()
            self._send(200, body)
            return
        self._send(404, b'{"error":"not_found"}')

    def _proxy(self, base: str, payload: bytes, timeout: float, route: str, streaming: bool) -> None:
        request = urllib.request.Request(base + self.path, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if not streaming:
                try:
                    body = response.read()
                except (OSError, TimeoutError) as exc:
                    self._send(504, json.dumps({"error": "upstream_response_timeout", "route": route, "detail": str(exc)}).encode(), route)
                    return
                self._send(response.status, body, route)
                return
            self.send_response(response.status)
            self.send_header("Content-Type", response.headers.get("Content-Type", "text/event-stream"))
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("X-Model-Route", route)
            self.end_headers()
            self.close_connection = True
            try:
                while True:
                    # read1 returns available SSE bytes without waiting for an
                    # entire 8 KiB buffer or connection close.
                    chunk = response.read1(8192)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                self.close_connection = True

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self._send(404, b'{"error":"not_found"}')
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)
        started = time.monotonic()
        try:
            streaming = json.loads(payload).get("stream") is True
        except (ValueError, AttributeError):
            self._send(400, b'{"error":"invalid_json"}')
            return
        try:
            self._proxy(BIG, payload, TIMEOUT, "big", streaming)
            return
        except (OSError, urllib.error.URLError, TimeoutError):
            pass
        try:
            self._proxy(SMALL, payload, 300, "small_fallback", streaming)
            return
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            body = json.dumps({"error": "no_model_backend", "detail": str(exc), "elapsed": time.monotonic() - started}).encode()
            self._send(503, body)

    def log_message(self, *_args: object) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
