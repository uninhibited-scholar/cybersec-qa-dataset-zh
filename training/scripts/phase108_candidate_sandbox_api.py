#!/usr/bin/env python3
"""Loopback-only OpenAI-shaped API for a sealed Phase108 candidate.

The server is a sandbox evaluator component, not a production service.  It
loads a caller-pinned base/adapter once, refuses non-loopback binding, rejects
tools, and never writes weights or binds the Phase91 production port.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from phase108_hf_adapter_smoke import attach_adapter


STATE: dict = {}
LOCK = threading.Lock()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(base: Path, adapter: Path, expected_adapter_sha256: str, scale: float) -> None:
    if file_hash(adapter) != expected_adapter_sha256:
        raise SystemExit("candidate adapter hash mismatch")
    use_cuda = torch.cuda.is_available()
    device_map = "cuda:0" if use_cuda else "cpu"
    if use_cuda:
        capability = torch.cuda.get_device_capability(0)
        dtype = torch.bfloat16 if capability >= (8, 0) else torch.float16
        print(json.dumps({"runtime_device": torch.cuda.get_device_name(0),
                          "compute_capability": capability,
                          "runtime_dtype": str(dtype)}, sort_keys=True), flush=True)
    else:
        dtype = torch.float32
        print(json.dumps({"runtime_device": "cpu", "runtime_dtype": str(dtype)}, sort_keys=True), flush=True)
    tokenizer = AutoTokenizer.from_pretrained(str(base), local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        str(base), torch_dtype=dtype, device_map=device_map, low_cpu_mem_usage=True,
        local_files_only=True, trust_remote_code=False,
    )
    projections = attach_adapter(model, adapter, scale=scale)
    model.eval()
    STATE.update(model=model, tokenizer=tokenizer,
                 device=model.get_input_embeddings().weight.device,
                 adapter_sha256=expected_adapter_sha256, projections=projections)


def generate(payload: dict) -> tuple[str, str]:
    if payload.get("tools") not in (None, []):
        raise ValueError("sandbox evaluator has no tools")
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages or any(
        not isinstance(row, dict) or row.get("role") not in {"system", "user", "assistant"}
        or not isinstance(row.get("content"), str) for row in messages
    ):
        raise ValueError("messages must be a non-empty standard chat sequence")
    requested = payload.get("max_tokens", 700)
    if not isinstance(requested, int) or requested < 1:
        raise ValueError("max_tokens must be a positive integer")
    max_new = min(requested, 700)
    temperature = payload.get("temperature", 0.12)
    top_p = payload.get("top_p", 0.9)
    if not isinstance(temperature, (int, float)) or not isinstance(top_p, (int, float)):
        raise ValueError("sampling controls must be numeric")
    tokenizer, model, device = STATE["tokenizer"], STATE["model"], STATE["device"]
    rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(rendered, return_tensors="pt").to(device)
    with LOCK, torch.inference_mode():
        generated = model.generate(
            **inputs, max_new_tokens=max_new, do_sample=temperature > 0,
            temperature=max(float(temperature), 1e-5), top_p=float(top_p),
            repetition_penalty=1.12,
        )
    tokens = generated[0, inputs["input_ids"].shape[1]:]
    text = tokenizer.decode(tokens, skip_special_tokens=True)
    return text, "length" if len(tokens) >= max_new else "stop"


class Handler(BaseHTTPRequestHandler):
    server_version = "Phase108Sandbox/1.0"

    def log_message(self, _format, *_args):
        # Do not log payloads/prompts or raw output to the scheduler log.
        return

    def json(self, status: int, body: dict) -> None:
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self.json(200, {"status": "ok", "sandbox": True})
        if self.path == "/v1/models":
            return self.json(200, {"data": [{"id": "phase108-candidate", "object": "model"}]})
        return self.json(404, {"error": {"message": "not found"}})

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            return self.json(404, {"error": {"message": "not found"}})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 2_000_000:
                raise ValueError("invalid request size")
            payload = json.loads(self.rfile.read(length))
            text, finish = generate(payload)
        except (ValueError, json.JSONDecodeError) as exc:
            return self.json(400, {"error": {"message": str(exc)}})
        except Exception:
            return self.json(500, {"error": {"message": "sandbox generation failed"}})
        choice = {"index": 0, "delta": {"content": text}, "finish_reason": finish}
        if payload.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            event = json.dumps({"id": "sandbox", "object": "chat.completion.chunk", "choices": [choice]}, ensure_ascii=False)
            self.wfile.write(f"data: {event}\n\ndata: [DONE]\n\n".encode()); self.wfile.flush()
            return
        return self.json(200, {"id": "sandbox", "object": "chat.completion", "choices": [{
            "index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": finish,
        }]})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--expected-adapter-sha256", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--scale", type=float, default=20.0)
    args = parser.parse_args()
    if args.port == 18765 or not 20000 <= args.port <= 29999:
        raise SystemExit("sandbox port must be in 20000-29999 and must not be the production port")
    load(args.base, args.adapter, args.expected_adapter_sha256, args.scale)
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(json.dumps({"sandbox_ready": True, "bind": f"127.0.0.1:{args.port}",
                      "adapter_sha256": STATE["adapter_sha256"],
                      "adapter_projections": STATE["projections"], "tools": []}), flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
