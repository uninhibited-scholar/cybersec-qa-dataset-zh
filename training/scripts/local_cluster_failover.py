#!/usr/bin/env python3
"""Localhost-only failover proxy for the GPU and CPU cluster tunnels."""
from __future__ import annotations

import http.client
import json
import os
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

TOKEN = os.environ["CLUSTER_MODEL_API_TOKEN"]
PRIMARY = os.environ.get("PRIMARY_URL", "http://127.0.0.1:19002").rstrip("/")
FALLBACK = os.environ.get("FALLBACK_URL", "http://127.0.0.1:19004").rstrip("/")
PORT = int(os.environ.get("FAILOVER_PORT", "19003"))


def request(base: str, path: str, payload: bytes | None, *, stream: bool = False):
    u = urlsplit(base)
    conn = http.client.HTTPConnection(u.hostname, u.port, timeout=360 if stream else 120)
    headers = {"Authorization": "Bearer " + TOKEN}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    conn.request("POST" if payload is not None else "GET", path, body=payload, headers=headers)
    return conn, conn.getresponse()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def send_json(self, status: int, obj: dict, route: str = "router") -> None:
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Model-Route", route)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            states = {}
            for name, base in (("big", PRIMARY), ("small_fallback", FALLBACK)):
                try:
                    c, r = request(base, "/health", None)
                    states[name] = 200 <= r.status < 300
                    r.read(); c.close()
                except (OSError, socket.timeout):
                    states[name] = False
            self.send_json(200 if any(states.values()) else 503, {"status": "ok" if any(states.values()) else "unavailable", **states})
            return
        if self.path == "/v1/models":
            self.send_json(200, {"object": "list", "data": [{"id": "qwen3-14b-bf16", "object": "model", "owned_by": "local-failover"}]})
            return
        self.send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self.send_json(404, {"error": "not_found"})
            return
        payload = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        try:
            streaming = json.loads(payload).get("stream") is True
        except (ValueError, AttributeError):
            self.send_json(400, {"error": "invalid_json"})
            return
        for base, route in ((PRIMARY, "big"), (FALLBACK, "small_fallback")):
            try:
                c, r = request(base, self.path, payload, stream=streaming)
                if not streaming:
                    body = r.read()
                    self.send_response(r.status)
                    self.send_header("Content-Type", r.getheader("Content-Type", "application/json"))
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("X-Model-Route", route)
                    self.end_headers(); self.wfile.write(body); c.close(); return
                self.send_response(r.status)
                self.send_header("Content-Type", r.getheader("Content-Type", "text/event-stream"))
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self.send_header("X-Model-Route", route)
                self.end_headers(); self.close_connection = True
                while True:
                    chunk = r.read1(8192)
                    if not chunk: break
                    self.wfile.write(chunk); self.wfile.flush()
                c.close(); return
            except (OSError, socket.timeout, http.client.HTTPException):
                continue
        self.send_json(503, {"error": "no_model_backend"}, "unavailable")

    def log_message(self, *_args: object) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
