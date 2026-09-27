from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from cluster_model_api_gateway import GatewayServer, Handler


TOKEN = "unit-test-token-" + "x" * 40


class FakeUpstreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"status": "ok", "path": self.path}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        size = int(self.headers.get("Content-Length", "0"))
        request_body = self.rfile.read(size)
        body = json.dumps({
            "choices": [{"message": {"content": "test reply"}}],
            "auth_forwarded": self.headers.get("Authorization") is not None,
            "received": json.loads(request_body),
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Model-Route", "small_fallback")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


class GatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstream = ThreadingHTTPServer(("127.0.0.1", 0), FakeUpstreamHandler)
        cls.upstream_thread = threading.Thread(target=cls.upstream.serve_forever, daemon=True)
        cls.upstream_thread.start()
        cls.gateway = GatewayServer(
            ("127.0.0.1", 0), Handler, token=TOKEN,
            allowed_source="127.0.0.1",
            upstream=f"http://127.0.0.1:{cls.upstream.server_port}",
        )
        cls.gateway_thread = threading.Thread(target=cls.gateway.serve_forever, daemon=True)
        cls.gateway_thread.start()
        cls.base = f"http://127.0.0.1:{cls.gateway.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.gateway.shutdown()
        cls.gateway.server_close()
        cls.upstream.shutdown()
        cls.upstream.server_close()

    def request(self, path, payload=None, authorization=None):
        headers = {}
        data = None
        if authorization is not None:
            headers["Authorization"] = authorization
        if payload is not None:
            data = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        req = Request(self.base + path, data=data, headers=headers)
        try:
            with urlopen(req, timeout=5) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def test_unauthenticated_health_rejected(self):
        status, body = self.request("/health")
        self.assertEqual(status, 401)
        self.assertEqual(body["error"], "unauthorized")

    def test_wrong_token_rejected(self):
        status, body = self.request("/v1/models", authorization="Bearer wrong")
        self.assertEqual(status, 401)
        self.assertEqual(body["error"], "unauthorized")

    def test_authorized_get_proxies(self):
        status, body = self.request("/health", authorization=f"Bearer {TOKEN}")
        self.assertEqual(status, 200)
        self.assertEqual(body["path"], "/health")

    def test_tool_metadata_is_stripped_without_claiming_execution(self):
        status, body = self.request(
            "/v1/chat/completions",
            {"messages": [{"role": "user", "content": "hello"}],
             "tools": [{"type": "function", "function": {"name": "x"}}]},
            f"Bearer {TOKEN}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["received"].get("tools"), None)

    def test_authorized_chat_proxies_without_forwarding_credentials(self):
        payload = {"messages": [{"role": "user", "content": "hello"}], "max_tokens": 8}
        headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
        req = Request(self.base + "/v1/chat/completions", data=json.dumps(payload).encode(), headers=headers)
        with urlopen(req, timeout=5) as response:
            status = response.status
            route = response.headers.get("X-Model-Route")
            body = json.loads(response.read())
        self.assertEqual(status, 200)
        self.assertEqual(route, "small_fallback")
        self.assertFalse(body["auth_forwarded"])
        self.assertEqual(body["received"], payload)


if __name__ == "__main__":
    unittest.main()
