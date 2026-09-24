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
            body = json.dumps({"status": "ok", "big": health(BIG), "small": health(SMALL)}).encode()
            self._send(200, body)
            return
        self._send(404, b'{"error":"not_found"}')

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self._send(404, b'{"error":"not_found"}')
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)
        started = time.monotonic()
        try:
            with urllib.request.urlopen(
                urllib.request.Request(BIG + self.path, data=payload, headers={"Content-Type": "application/json"}),
                timeout=TIMEOUT,
            ) as response:
                data = response.read()
                self._send(response.status, data, "big")
                return
        except (OSError, urllib.error.URLError, TimeoutError):
            pass
        try:
            with urllib.request.urlopen(
                urllib.request.Request(SMALL + self.path, data=payload, headers={"Content-Type": "application/json"}),
                timeout=60,
            ) as response:
                data = response.read()
                self._send(response.status, data, "small_fallback")
                return
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            body = json.dumps({"error": "no_model_backend", "detail": str(exc), "elapsed": time.monotonic() - started}).encode()
            self._send(503, body)

    def log_message(self, *_args: object) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
