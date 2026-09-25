#!/usr/bin/env python3
"""Minimal loopback OpenAI-compatible CPU fallback for a small model."""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

MODEL = os.environ["SMALL_MODEL_PATH"]
PORT = int(os.environ.get("SMALL_PORT", "19001"))
TOKENIZER = AutoTokenizer.from_pretrained(MODEL)
MODEL_OBJ = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32, device_map={"": "cpu"})
MODEL_OBJ.eval()
MODEL_ID = os.environ.get("MODEL_ID", "qwen3-1.7b-cpu")
GENERATION_LOCK = threading.Lock()


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
            self.send_json(200, {"status": "ok", "model": MODEL_ID, "device": "cpu"})
        elif self.path == "/v1/models":
            self.send_json(200, {"object": "list", "data": [{"id": MODEL_ID, "object": "model", "owned_by": "local"}]})
        else:
            self.send_json(404, {"error": "not_found"})

    def _stream(self, request: dict, inputs: dict, limit: int) -> None:
        streamer = TextIteratorStreamer(TOKENIZER, skip_prompt=True, skip_special_tokens=True, timeout=300)
        temperature = float(request.get("temperature", 0.0))
        generation = {"max_new_tokens": limit, "do_sample": temperature > 0, "streamer": streamer}
        if temperature > 0:
            generation["temperature"] = temperature
            generation["top_p"] = float(request.get("top_p", 1.0))
        errors: list[Exception] = []

        def generate() -> None:
            try:
                with GENERATION_LOCK, torch.inference_mode():
                    MODEL_OBJ.generate(**inputs, **generation)
            except Exception as exc:
                errors.append(exc)
                streamer.end()

        response_id = "chatcmpl-" + uuid.uuid4().hex[:16]
        created = int(time.time())
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

        def emit(data: dict | str) -> None:
            body = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
            self.wfile.write(("data: " + body + "\n\n").encode())
            self.wfile.flush()

        emit({"id": response_id, "object": "chat.completion.chunk", "created": created, "model": MODEL_ID, "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]})
        worker = threading.Thread(target=generate, daemon=True)
        worker.start()
        try:
            for piece in streamer:
                if piece:
                    emit({"id": response_id, "object": "chat.completion.chunk", "created": created, "model": MODEL_ID, "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}]})
        except (BrokenPipeError, ConnectionResetError):
            return
        worker.join()
        if errors:
            emit({"error": {"message": type(errors[0]).__name__, "type": "server_error"}})
        emit({"id": response_id, "object": "chat.completion.chunk", "created": created, "model": MODEL_ID, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})
        emit("[DONE]")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self.send_json(404, {"error": "not_found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length))
        messages = request.get("messages", [])
        # Qwen3's default chat template enables a <think> channel.  This local
        # fallback is intended to be a directly consumable chat API, so ask the
        # tokenizer for its non-thinking form instead of returning internal
        # reasoning text as the user-facing completion.
        prompt = TOKENIZER.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = TOKENIZER(prompt, return_tensors="pt")
        limit = min(int(request.get("max_tokens", request.get("max_new_tokens", 256))), 512)
        started = time.monotonic()
        if request.get("stream") is True:
            self._stream(request, inputs, limit)
            return
        with GENERATION_LOCK, torch.inference_mode():
            output = MODEL_OBJ.generate(**inputs, max_new_tokens=limit, do_sample=False)
        text = TOKENIZER.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        token_count = int(output.shape[1] - inputs["input_ids"].shape[1])
        self.send_json(200, {"id": "cpu-fallback", "object": "chat.completion", "created": int(time.time()), "model": MODEL_ID, "choices": [{"index": 0, "message": {"role": "assistant", "content": text.strip()}, "finish_reason": "length" if token_count >= limit else "stop"}], "usage": {"completion_tokens": token_count, "elapsed_seconds": time.monotonic() - started}})

    def log_message(self, *_args: object) -> None:
        return


ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
