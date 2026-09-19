#!/usr/bin/env python3
"""Collect blinded Phase 107 v0.2 outputs through SSH-only API forwards.

Reads the ignored case manifest, never opens answer keys, and never prints or
stores the Phase 91 credential. Raw outputs and identity mapping must stay out
of Git. No evaluator-client retries are made.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import random
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


SYSTEM_PROMPT = (
    "你是运行在用户 Mac mini 上、通过 API 接入 DeepSeek Harness 的本地网安特化语言模型。"
    "严格区分模型、知识库和外层工具；不得虚构未接入、未执行或未返回结果的能力。"
    "正常回答用户提出的分析问题；证据不足时指出具体未知项，但不要用固定拒答替代可完成的文本分析。"
    "默认使用清晰 Markdown：先给结论，再按必要的小标题和要点展开；避免重复、空泛套话和过深层级。"
    "不要复述格式指令，也不要把长篇正文塞进工具参数。严禁编造上下文未提供的日志、指标、文件、函数、"
    "错误结构、百分比、测试次数或编号；没有证据的细节必须明确写为未知；普通知识、数学、历史和地理问题"
    "可以直接回答，不要套用网安拒答模板。结构化长答优先保证所有要求部分完整结束：每部分最多三个简洁要点，"
    "除非用户明确要求展开，总长度控制在约一千个中文字内。\n"
    "本轮没有向你提供工具。请只输出完整的纯文本 Markdown 回答，不得输出 <tool_call>、工具名或规划模式标记。"
)
SYSTEMS = ("phase91", "gptoss20b", "gemma4_26b")
EXPECTED_PHASE91_WORKER_SHA256 = "a4936301d54bb08bf8b7fa82847e090bbba827c6815513dd5d2d3ae88f7302cb"
EXPECTED_SYSTEM_PROMPT_SHA256 = "6017e9aab198e717f3d61082e08e45ca6fd0afa2158f750c43e1966110efe57e"
OUT_DIR: Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_no_tool_system(worker_source: bytes) -> str:
    """Reconstruct the worker's static no-tool system content without executing it."""
    tree = ast.parse(worker_source.decode("utf-8"))
    render = next((node for node in tree.body
                   if isinstance(node, ast.FunctionDef) and node.name == "render_prompt"), None)
    if render is None:
        raise ValueError("Phase 91 worker has no render_prompt function")

    parts_assignment = next((node for node in render.body
                             if isinstance(node, ast.Assign)
                             and any(isinstance(target, ast.Name) and target.id == "system_parts"
                                     for target in node.targets)), None)
    if parts_assignment is None:
        raise ValueError("cannot locate worker system-prompt construction")
    base_parts = ast.literal_eval(parts_assignment.value)
    if not isinstance(base_parts, list) or not base_parts or not all(isinstance(x, str) for x in base_parts):
        raise ValueError("unsupported worker base system-prompt shape")

    tools_branch = next((node for node in render.body
                         if isinstance(node, ast.If)
                         and isinstance(node.test, ast.Name) and node.test.id == "tools"), None)
    if tools_branch is None:
        raise ValueError("cannot locate worker no-tools prompt branch")
    no_tool_clauses = [
        ast.literal_eval(call.args[0])
        for statement in tools_branch.orelse
        for call in ast.walk(statement)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "system_parts"
        and call.func.attr == "append"
        and call.args
        and isinstance(call.args[0], ast.Constant)
        and isinstance(call.args[0].value, str)
    ]
    if len(no_tool_clauses) != 1:
        raise ValueError("unsupported worker no-tools prompt shape")

    newline_join = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "join"
        and isinstance(node.func.value, ast.Constant)
        and node.func.value.value == "\n"
        and node.args
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "system_parts"
        for node in ast.walk(render)
    )
    if not newline_join:
        raise ValueError("unsupported worker system-prompt join semantics")
    return "\n".join([*base_parts, no_tool_clauses[0]])


def validate_prompt_parity(worker_source: bytes, reference_prompt: str) -> dict:
    worker_hash = sha256_bytes(worker_source)
    if worker_hash != EXPECTED_PHASE91_WORKER_SHA256:
        raise ValueError(f"Phase 91 worker hash changed: {worker_hash}")
    reference_hash = sha256_bytes(reference_prompt.encode("utf-8"))
    if reference_hash != EXPECTED_SYSTEM_PROMPT_SHA256:
        raise ValueError(f"reference system-prompt hash changed: {reference_hash}")
    effective_prompt = extract_no_tool_system(worker_source)
    effective_hash = sha256_bytes(effective_prompt.encode("utf-8"))
    if effective_prompt != reference_prompt:
        raise ValueError(
            "effective Phase 91 no-tool prompt differs from reference prompt; "
            f"effective_sha256={effective_hash} reference_sha256={reference_hash}"
        )
    return {"worker_sha256": worker_hash, "system_prompt_sha256": effective_hash}


def atomic_json(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(path)


def start_tunnel(command: list[str], label: str) -> subprocess.Popen:
    log = (OUT_DIR / f"tunnel-{label}.stderr.log").open("ab")
    p = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=log, start_new_session=True)
    p._phase107_log = log
    return p


def wait_port(port: int, proc: subprocess.Popen, label: str) -> None:
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"SSH tunnel exited for {label}")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.25)
    raise TimeoutError(f"SSH tunnel port unavailable for {label}")


def get_json(url: str, token: str | None = None, timeout: int = 15) -> tuple[int, dict | None, str | None]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        return e.code, None, "http_error"
    except Exception as e:
        return 0, None, type(e).__name__


def stream_completion(url: str, payload: dict, token: str | None) -> dict:
    headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=json.dumps(payload, ensure_ascii=False).encode(), headers=headers)
    start = time.monotonic()
    first_content = None
    chunks: list[str] = []
    finish = None
    status = None
    got_done = False
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            status = r.status
            for raw in r:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                event = line[5:].strip()
                if event == "[DONE]":
                    got_done = True
                    break
                try:
                    choice = json.loads(event).get("choices", [{}])[0]
                    delta = choice.get("delta", {}) or {}
                    piece = delta.get("content")
                    if isinstance(piece, str) and piece:
                        if first_content is None:
                            first_content = time.monotonic() - start
                        chunks.append(piece)
                    if choice.get("finish_reason") is not None:
                        finish = choice["finish_reason"]
                except (ValueError, TypeError, IndexError, AttributeError):
                    return {"transport_status": status, "classification": "parse_error", "content": "",
                            "finish_reason": finish, "first_content_s": first_content,
                            "total_s": time.monotonic() - start}
        content = "".join(chunks)
        classification = "ok" if content.strip() else "empty"
        if not got_done and classification == "ok":
            classification = "incomplete_stream"
        return {"transport_status": status, "classification": classification,
                "content": content, "finish_reason": finish, "first_content_s": first_content,
                "total_s": time.monotonic() - start}
    except urllib.error.HTTPError as e:
        return {"transport_status": e.code, "classification": "http_error", "content": "",
                "finish_reason": finish, "first_content_s": first_content,
                "total_s": time.monotonic() - start}
    except TimeoutError:
        return {"transport_status": status, "classification": "timeout", "content": "".join(chunks),
                "finish_reason": finish, "first_content_s": first_content,
                "total_s": time.monotonic() - start}
    except Exception as e:
        return {"transport_status": status, "classification": "transport_error:" + type(e).__name__,
                "content": "".join(chunks), "finish_reason": finish, "first_content_s": first_content,
                "total_s": time.monotonic() - start}


def main() -> int:
    global OUT_DIR
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--mini-user", default="jiehan")
    ap.add_argument("--mini-host", default="192.168.31.212")
    ap.add_argument("--cluster-user", default="zj225")
    ap.add_argument("--cluster-host", default="slurmc.ie.cuhk.edu.hk")
    ap.add_argument("--seed", type=int, default=20260919)
    args = ap.parse_args()
    OUT_DIR = args.outdir.expanduser().resolve()
    OUT_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(OUT_DIR, 0o700)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if len(cases) != 320 or any(c.get("suite_version") != "phase107-v0.2" for c in cases):
        raise SystemExit("preflight failed: expected exactly 320 Phase 107 v0.2 cases")
    if len({c.get("id") for c in cases}) != 320 or any(not c.get("messages") for c in cases):
        raise SystemExit("preflight failed: duplicate IDs or missing messages")

    worker_source_result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
         f"{args.mini_user}@{args.mini_host}", "cat /Users/jiehan/cyber-agent/phase91_worker.py"],
        capture_output=True, timeout=15,
    )
    if worker_source_result.returncode != 0:
        raise SystemExit("preflight failed: cannot read pinned Phase 91 worker for prompt-parity check")
    try:
        prompt_parity = validate_prompt_parity(worker_source_result.stdout, SYSTEM_PROMPT)
    except (SyntaxError, ValueError) as exc:
        raise SystemExit(f"preflight failed: {exc}") from exc
    del worker_source_result

    sealed_path = OUT_DIR / "sealed-identities.json"
    if sealed_path.exists():
        aliases = json.loads(sealed_path.read_text(encoding="utf-8"))["alias_to_system"]
    else:
        shuffled = list(SYSTEMS)
        secrets.SystemRandom().shuffle(shuffled)
        aliases = dict(zip(("A", "B", "C"), shuffled))
        atomic_json(sealed_path, {"alias_to_system": aliases,
                                  "warning": "Do not open until blind adjudication is complete."})
    system_alias = {v: k for k, v in aliases.items()}
    result_path = OUT_DIR / "blind-responses.jsonl"
    existing = []
    if result_path.exists():
        with result_path.open(encoding="utf-8") as f:
            existing = [json.loads(x) for x in f if x.strip()]
    completed = {(r["case_id"], r["alias"]) for r in existing}

    processes: list[subprocess.Popen] = []
    try:
        p = start_tunnel(["ssh", "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes", "-N",
                          "-L", "127.0.0.1:18765:127.0.0.1:18765",
                          f"{args.mini_user}@{args.mini_host}"], "mini")
        processes.append(p); wait_port(18765, p, "mini")
        p = start_tunnel(["ssh", "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes", "-N",
                          "-L", "127.0.0.1:18181:127.0.0.1:39081",
                          "-L", "127.0.0.1:18182:127.0.0.1:39082",
                          f"{args.cluster_user}@{args.cluster_host}"], "cluster")
        processes.append(p); wait_port(18181, p, "GPT-OSS"); wait_port(18182, p, "Gemma")
        secret = subprocess.run(["ssh", "-o", "BatchMode=yes", f"{args.mini_user}@{args.mini_host}",
                                 "cat /Users/jiehan/.config/cyber-agent/api-token"],
                                check=True, capture_output=True, timeout=15).stdout
        token = secret.decode("utf-8").strip()
        del secret
        if len(token) < 16:
            raise RuntimeError("credential source returned invalid data")

        endpoints = {
            "phase91": ("http://127.0.0.1:18765/v1/chat/completions", token),
            "gptoss20b": ("http://127.0.0.1:18181/v1/chat/completions", None),
            "gemma4_26b": ("http://127.0.0.1:18182/v1/chat/completions", None),
        }
        for system, (url, auth) in endpoints.items():
            status, _body, error = get_json(url.rsplit("/v1/", 1)[0] + "/health", auth)
            if status != 200 or error:
                raise RuntimeError(f"health preflight failed for {system}: status={status}, type={error}")
        status, _body, error = get_json("http://127.0.0.1:18765/v1/models", token)
        if status != 200 or error:
            raise RuntimeError(f"authorized Phase 91 preflight failed: status={status}, type={error}")

        atomic_json(OUT_DIR / "blind-run-manifest.json", {
            "suite_version": "phase107-v0.2", "case_count": len(cases),
            "suite_sha256": sha256(args.cases),
            "protocol": "phase107-inference-protocol-v0.1+corrigendum-v0.1.1",
            "run_seed": args.seed, "input_field": "messages", "answer_keys_loaded": False,
            "max_tokens": 700, "temperature": 0.12, "top_p": 0.9,
            "repeat_penalty": 1.12, "repeat_context": 128,
            "phase91_prompt_parity": prompt_parity,
            "reference_top_k": 0, "reference_min_p": 0.0, "reference_dry_multiplier": 0.0,
            "tools": [], "client_retries": 0, "timeout_seconds": 300,
            "phase91_streaming_caveat": "full answer emitted in one SSE content chunk; first_content_s is not token-level TTFT",
            "response_file": result_path.name, "alias_map": "sealed-identities.json",
        })
        rng = random.Random(args.seed)
        pending = list(cases); rng.shuffle(pending)
        total = len(cases) * len(SYSTEMS)
        count = len(completed)
        for index, case in enumerate(pending, 1):
            order_rng = random.Random(args.seed + int(hashlib.sha256(case["id"].encode()).hexdigest()[:8], 16))
            arm_order = list(SYSTEMS); order_rng.shuffle(arm_order)
            for system in arm_order:
                alias = system_alias[system]
                if (case["id"], alias) in completed:
                    continue
                url, auth = endpoints[system]
                messages = list(case["messages"])
                if system != "phase91":
                    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
                payload = {"model": "qwen-cyber-agent" if system == "phase91" else "local-reference",
                           "messages": messages, "tools": [], "max_tokens": 700,
                           "temperature": 0.12, "top_p": 0.9, "stream": True}
                result = stream_completion(url, payload, auth)
                content = result.pop("content")
                classification = result.get("classification")
                if result.get("finish_reason") == "length" and classification == "ok":
                    classification = "truncated"
                row = {"case_id": case["id"], "category": case["category"], "alias": alias,
                       "content": content,
                       "arm_order_for_case": [system_alias[s] for s in arm_order],
                       **result, "classification": classification}
                with result_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    f.flush(); os.fsync(f.fileno())
                os.chmod(result_path, 0o600)
                completed.add((case["id"], alias)); count += 1
                print(f"progress={count}/{total} case={index}/{len(cases)} alias={alias} class={row['classification']}", flush=True)
        atomic_json(OUT_DIR / "sealed-run-details.json", {
            "alias_to_system": aliases,
            "reference_model_hashes": {
                "gptoss20b": "10fe673de12c20b74b8d670a9fdf0fd36b43b0a86ffc04daeb175c0a2b98c4f9",
                "gemma4_26b": "f2c28b3dc4776931ac6f879e11f203dec637ea0f14267a86ec8f6165f63f293f",
            },
            "reference_runtime": "llama.cpp b11046, native templates, reasoning auto",
            "phase91_worker_sha256": "a4936301d54bb08bf8b7fa82847e090bbba827c6815513dd5d2d3ae88f7302cb",
            "phase91_base": "Qwen3-4B-mlx-4bit-phase3-wrapper",
            "phase91_adapter": "phase99-multiturn-candidate",
            "model_identity_release_gate": "reviewer calibration and blind critical-failure adjudication complete",
        })
        print(f"complete={count}/{total}; raw output and mapping remain outside Git", flush=True)
        return 0
    finally:
        for p in reversed(processes):
            p.terminate()
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
            getattr(p, "_phase107_log", None) and p._phase107_log.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("interrupted; finished cases are durable and resumable", file=sys.stderr)
        raise SystemExit(130)
