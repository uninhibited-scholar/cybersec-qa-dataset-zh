#!/usr/bin/env python3
"""Minimal loopback OpenAI-compatible CPU fallback for a small model."""
from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = os.environ["SMALL_MODEL_PATH"]
PORT = int(os.environ.get("SMALL_PORT", "19001"))
TOKENIZER = AutoTokenizer.from_pretrained(MODEL)
MODEL_OBJ = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32, device_map={"": "cpu"})
MODEL_OBJ.eval()


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self.send_json(200, {"status": "ok", "model": MODEL})
        else:
            self.send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self.send_json(404, {"error": "not_found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length))
        messages = request.get("messages", [])
        prompt = TOKENIZER.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = TOKENIZER(prompt, return_tensors="pt")
        limit = min(int(request.get("max_tokens", request.get("max_new_tokens", 256))), 512)
        started = time.monotonic()
        with torch.inference_mode():
            output = MODEL_OBJ.generate(**inputs, max_new_tokens=limit, do_sample=False)
        text = TOKENIZER.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        self.send_json(200, {"id": "cpu-fallback", "object": "chat.completion", "created": int(time.time()), "model": MODEL, "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}], "usage": {"completion_tokens": int(output.shape[1] - inputs["input_ids"].shape[1]), "elapsed_seconds": time.monotonic() - started}})

    def log_message(self, *_args: object) -> None:
        return


ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
