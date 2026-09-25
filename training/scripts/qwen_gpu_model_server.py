#!/usr/bin/env python3
"""Minimal loopback OpenAI-compatible server for a local CUDA Transformers model."""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

MODEL_PATH = os.environ["MODEL_PATH"]
MODEL_ID = os.environ.get("MODEL_ID", "qwen3-14b-bf16")
PORT = int(os.environ.get("MODEL_PORT", "19000"))
MAX_BODY_BYTES = int(os.environ.get("MAX_BODY_BYTES", str(1024 * 1024)))
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", "512"))

TOKENIZER = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
MODEL = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="cuda:0",
    local_files_only=True,
    low_cpu_mem_usage=True,
)
MODEL.eval()
GENERATION_LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self.send_json(200, {"status": "ok", "model": MODEL_ID, "device": "cuda:0"})
        elif self.path == "/v1/models":
            self.send_json(200, {"object": "list", "data": [{"id": MODEL_ID, "object": "model", "owned_by": "local"}]})
        else:
            self.send_json(404, {"error": {"message": "not_found", "type": "invalid_request_error"}})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self.send_json(404, {"error": {"message": "not_found", "type": "invalid_request_error"}})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > MAX_BODY_BYTES:
                self.send_json(413, {"error": {"message": "request_body_out_of_range", "type": "invalid_request_error"}})
                return
            request = json.loads(self.rfile.read(length))
            messages = request.get("messages")
            if not isinstance(messages, list) or not messages:
                self.send_json(400, {"error": {"message": "messages_required", "type": "invalid_request_error"}})
                return
            max_tokens = max(1, min(int(request.get("max_tokens", request.get("max_completion_tokens", MAX_NEW_TOKENS))), MAX_NEW_TOKENS))
            prompt = TOKENIZER.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            inputs = TOKENIZER(prompt, return_tensors="pt").to("cuda:0")
            temperature = float(request.get("temperature", 0.0))
            generation = {"max_new_tokens": max_tokens, "do_sample": temperature > 0}
            if temperature > 0:
                generation["temperature"] = temperature
                generation["top_p"] = float(request.get("top_p", 1.0))
            started = time.monotonic()
            if request.get("stream") is True:
                self._stream(request, inputs, generation)
                return
            with GENERATION_LOCK, torch.inference_mode():
                output = MODEL.generate(**inputs, **generation)
            elapsed = time.monotonic() - started
            token_count = int(output.shape[1] - inputs["input_ids"].shape[1])
            answer = TOKENIZER.decode(output[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
            self.send_json(200, {
                "id": "chatcmpl-" + uuid.uuid4().hex[:16],
                "object": "chat.completion",
                "created": int(time.time()),
                "model": MODEL_ID,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": answer}, "finish_reason": "length" if token_count >= max_tokens else "stop"}],
                "usage": {"prompt_tokens": int(inputs["input_ids"].shape[1]), "completion_tokens": token_count, "total_tokens": int(inputs["input_ids"].shape[1]) + token_count, "elapsed_seconds": elapsed},
            })
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self.send_json(400, {"error": {"message": str(exc), "type": "invalid_request_error"}})
        except Exception as exc:
            self.send_json(500, {"error": {"message": type(exc).__name__, "type": "server_error"}})

    def _stream(self, request: dict, inputs: dict, generation: dict) -> None:
        streamer = TextIteratorStreamer(TOKENIZER, skip_prompt=True, skip_special_tokens=True, timeout=300)
        generation = {**generation, "streamer": streamer}
        errors: list[Exception] = []

        def generate() -> None:
            try:
                with GENERATION_LOCK, torch.inference_mode():
                    MODEL.generate(**inputs, **generation)
            except Exception as exc:
                errors.append(exc)
                # Ensure the response iterator unblocks if generation fails.
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
        except (BrokenPipeError, ConnectionResetError, OSError):
            # Generation is not cancellable through this minimal smoke server;
            # wait so its lock and GPU work are released before accepting the
            # next request as healthy.
            worker.join()
            return
        worker.join()
        if errors:
            emit({"error": {"message": type(errors[0]).__name__, "type": "server_error"}})
        emit({"id": response_id, "object": "chat.completion.chunk", "created": created, "model": MODEL_ID, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})
        emit("[DONE]")

    def log_message(self, *_args: object) -> None:
        return


ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
