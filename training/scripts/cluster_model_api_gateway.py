#!/usr/bin/env python3
"""Authenticated, source-restricted gateway for a loopback model API.

This process is intended to run on the allocated compute node, not the Slurm
controller. The model API remains bound to node loopback; this gateway binds
only to the node's private interface and is intended to be reached through an
SSH local forward terminating at the controller. It never logs request or
response bodies and does not implement model tools/function calling.
"""
from __future__ import annotations

import argparse
import hmac
import ipaddress
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MAX_BODY_BYTES = 2 * 1024 * 1024
ALLOWED_PATHS = {"/health", "/v1/models", "/v1/chat/completions"}


class GatewayServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address, handler, *, token: str, allowed_source: str,
                 upstream: str, timeout: float = 360.0):
        self.api_token = token
        self.allowed_source = str(ipaddress.ip_address(allowed_source))
        self.upstream = upstream.rstrip("/")
        self.upstream_timeout = timeout
        super().__init__(address, handler)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ClusterModelGateway/1.0"

    def log_message(self, *_args):
        # Request paths, headers, prompts and model output are not logged.
        return

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def _authorized(self) -> bool:
        remote = self.client_address[0]
        try:
            remote = str(ipaddress.ip_address(remote))
        except ValueError:
            self._json(403, {"error": "source_not_allowed"})
            return False
        if remote != self.server.allowed_source:
            self._json(403, {"error": "source_not_allowed"})
            return False
        expected = "Bearer " + self.server.api_token
        if not hmac.compare_digest(self.headers.get("Authorization", ""), expected):
            self._json(401, {"error": "unauthorized"})
            return False
        return True

    def _proxy(self, body: bytes | None = None) -> None:
        path = self.path
        if path not in ALLOWED_PATHS:
            return self._json(404, {"error": "not_found"})
        headers = {}
        if body is not None:
            headers["Content-Type"] = self.headers.get("Content-Type", "application/json")
            headers["Accept"] = "text/event-stream" if self.headers.get("Accept", "").lower() == "text/event-stream" else "application/json"
        request = Request(self.server.upstream + path, data=body, headers=headers)
        try:
            response = urlopen(request, timeout=self.server.upstream_timeout)
        except HTTPError as error:
            response = error
        except (URLError, TimeoutError, OSError):
            return self._json(502, {"error": "upstream_unavailable"})

        with response:
            content_type = response.headers.get("Content-Type", "application/json")
            streaming = body is not None and "text/event-stream" in content_type.lower()
            if streaming:
                payload = None
            else:
                payload = response.read(MAX_BODY_BYTES + 1)
                if len(payload) > MAX_BODY_BYTES:
                    return self._json(502, {"error": "upstream_response_too_large"})
            self.send_response(response.status)
            self.send_header("Content-Type", content_type)
            # Preserve the router's explicit model-route label so a fallback
            # answer is never silently presented as the primary model's output.
            if response.headers.get("X-Model-Route"):
                self.send_header("X-Model-Route", response.headers["X-Model-Route"])
            if response.headers.get("Cache-Control"):
                self.send_header("Cache-Control", response.headers["Cache-Control"])
            if streaming:
                self.send_header("Connection", "close")
                self.end_headers()
                self.close_connection = True
                try:
                    while True:
                        chunk = response.read1(8192)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    self.close_connection = True
                return
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(payload)
            self.close_connection = True

    def do_GET(self):
        if not self._authorized():
            return
        self._proxy()

    def do_POST(self):
        if not self._authorized():
            return
        if self.path != "/v1/chat/completions":
            return self._json(404, {"error": "not_found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._json(400, {"error": "invalid_content_length"})
        if length < 1 or length > MAX_BODY_BYTES:
            return self._json(413, {"error": "request_body_out_of_range"})
        body = self.rfile.read(length)
        if len(body) != length:
            return self._json(400, {"error": "incomplete_request_body"})
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._json(400, {"error": "invalid_json"})
        if not isinstance(payload, dict):
            return self._json(400, {"error": "invalid_request"})
        # Kimi Code always includes its tool catalog. This endpoint has no
        # tool executor, so remove tool metadata before forwarding instead of
        # claiming support or failing an otherwise valid text completion.
        if payload.get("tools") not in (None, []) or payload.get("functions") not in (None, []):
            payload = dict(payload)
            for key in ("tools", "functions", "tool_choice", "function_call", "parallel_tool_calls"):
                payload.pop(key, None)
            body = json.dumps(payload, separators=(",", ":")).encode()
        self._proxy(body)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind-ip", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--allowed-source", required=True,
                        help="Exact private IP of the SSH controller that reaches this gateway")
    parser.add_argument("--upstream", default="http://127.0.0.1:28603")
    parser.add_argument("--token-env", default="CLUSTER_MODEL_API_TOKEN")
    args = parser.parse_args()
    bind_ip = ipaddress.ip_address(args.bind_ip)
    if not bind_ip.is_private or bind_ip.is_loopback or bind_ip.is_unspecified:
        raise SystemExit("gateway must bind an explicit private, non-loopback node IP")
    if not 20000 <= args.port <= 65535:
        raise SystemExit("gateway port must be in 20000..65535")
    source_ip = ipaddress.ip_address(args.allowed_source)
    if not source_ip.is_private:
        raise SystemExit("allowed source must be a private IP")
    token = os.environ.get(args.token_env, "")
    if len(token) < 32:
        raise SystemExit("API token must be supplied through the environment and be at least 32 characters")
    server = GatewayServer((str(bind_ip), args.port), Handler, token=token,
                           allowed_source=str(source_ip), upstream=args.upstream)
    print(json.dumps({"gateway_ready": True, "bind_ip": str(bind_ip),
                      "port": args.port, "allowed_source": str(source_ip),
                      "upstream": args.upstream, "auth": "bearer_required",
                      "tools_supported": False}), flush=True)
    server.serve_forever(poll_interval=0.5)


if __name__ == "__main__":
    main()
