#!/usr/bin/env python3
"""Local protocol tests for the dual-model router; no model weights required."""
from __future__ import annotations

import importlib.util
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROUTER_PATH = Path(__file__).with_name("dual_model_router.py")
SPEC = importlib.util.spec_from_file_location("dual_model_router", ROUTER_PATH)
assert SPEC and SPEC.loader
router = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(router)


class BackendHandler(BaseHTTPRequestHandler):
    content_type = "text/event-stream"
    label = "backend"

    def do_GET(self) -> None:  # noqa: N802
        body = b'{"status":"ok"}'
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        _ = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if self.headers.get("Accept") == "text/event-stream":
            body = (
                'data: {"choices":[{"delta":{"content":"hello"}}]}\n\n'
                "data: [DONE]\n\n"
            ).encode()
        else:
            body = json.dumps({"choices": [{"message": {"content": "hello"}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", self.content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


class RouterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.big = ThreadingHTTPServer(("127.0.0.1", 0), BackendHandler)
        cls.small = ThreadingHTTPServer(("127.0.0.1", 0), BackendHandler)
        cls.router = ThreadingHTTPServer(("127.0.0.1", 0), router.Handler)
        cls.threads = [
            threading.Thread(target=s.serve_forever, daemon=True)
            for s in (cls.big, cls.small, cls.router)
        ]
        for thread in cls.threads:
            thread.start()
        router.BIG = f"http://127.0.0.1:{cls.big.server_port}"
        router.SMALL = f"http://127.0.0.1:{cls.small.server_port}"
        router.TIMEOUT = 1

    @classmethod
    def tearDownClass(cls) -> None:
        for server in (cls.router, cls.small, cls.big):
            server.shutdown()
            server.server_close()
        for thread in cls.threads:
            thread.join(timeout=2)

    def call(self, streaming: bool) -> tuple[object, bytes]:
        body = json.dumps({"messages": [{"role": "user", "content": "test"}], "stream": streaming}).encode()
        request = Request(f"http://127.0.0.1:{self.router.server_port}/v1/chat/completions", data=body, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=5) as response:
            return response, response.read()

    def test_streaming_big_backend(self) -> None:
        BackendHandler.content_type = "text/event-stream"
        response, body = self.call(True)
        self.assertEqual(response.headers.get("X-Model-Route"), "big")
        self.assertIn(b"hello", body)
        self.assertIn(b"data: [DONE]", body)

    def test_nonstream_big_backend(self) -> None:
        response, body = self.call(False)
        self.assertEqual(response.headers.get("X-Model-Route"), "big")
        self.assertIn(b'"content": "hello"', body)

    def test_fallback_after_connection_failure(self) -> None:
        router.BIG = "http://127.0.0.1:1"
        response, body = self.call(True)
        self.assertEqual(response.headers.get("X-Model-Route"), "small_fallback")
        self.assertIn(b"hello", body)
        self.assertIn(b"data: [DONE]", body)
        router.BIG = f"http://127.0.0.1:{self.big.server_port}"

    def test_stream_protocol_mismatch_is_not_mislabeled_as_fallback(self) -> None:
        BackendHandler.content_type = "application/json"
        with self.assertRaises(HTTPError) as ctx:
            self.call(True)
        self.assertEqual(ctx.exception.code, 502)
        self.assertEqual(ctx.exception.headers.get("X-Model-Route"), "big")
        ctx.exception.close()
        BackendHandler.content_type = "text/event-stream"


if __name__ == "__main__":
    unittest.main()
