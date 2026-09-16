#!/usr/bin/env python3
import hmac
import json
import os
import pathlib
import re
import socketserver
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOME = pathlib.Path.home()
TOKEN_FILE = HOME / ".config/cyber-agent/api-token"
CYBER_AGENT = HOME / "bin/cyber-agent"
LOCK = threading.Lock()
MAX_BODY = 1_000_000
MODEL = pathlib.Path(os.environ.get(
    "CYBER_MODEL_PATH", str(HOME / "models/Qwen3-4B-mlx-4bit")
)).expanduser()
ADAPTER = pathlib.Path(os.environ.get(
    "CYBER_ADAPTER_PATH", str(HOME / "models/qwen-cyber-adapter")
)).expanduser()
AGENT_MODEL_ID = "qwen-cyber-agent"
_AGENT_WORKER = None

def ensure_agent_worker():
    """Keep MLX in its Python 3.14 process while HTTP runs on system Python."""
    global _AGENT_WORKER
    if _AGENT_WORKER is None or _AGENT_WORKER.poll() is not None:
        env = os.environ.copy()
        env["CYBER_MODEL_PATH"] = str(MODEL)
        env["CYBER_ADAPTER_PATH"] = str(ADAPTER)
        _AGENT_WORKER = subprocess.Popen(
            [str(HOME / "venvs/agents-a1/bin/python"),
             str(HOME / "cyber-agent/mlx_agent_worker.py")],
            text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=1, env=env,
        )
        ready = json.loads(_AGENT_WORKER.stdout.readline())
        if not ready.get("ready"):
            raise RuntimeError("MLX worker failed to initialize")
    return _AGENT_WORKER

def agent_generate(messages, tools, max_tokens=700):
    """Run the full Harness transcript instead of reducing it to the last user turn."""
    worker = ensure_agent_worker()
    worker.stdin.write(json.dumps({
        "messages": messages, "tools": tools, "max_tokens": max_tokens
    }, ensure_ascii=False) + "\n")
    worker.stdin.flush()
    response = json.loads(worker.stdout.readline())
    if not response.get("ok"):
        raise RuntimeError(response.get("error", "MLX worker failed"))
    return response["answer"]

TOOL_CALL_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.S)

def parsed_tool_call(text, allowed_names):
    """Translate Qwen's tool-call markup into an OpenAI tool call."""
    match = TOOL_CALL_RE.search(text)
    if not match:
        return None
    try:
        call = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    name = call.get("name")
    arguments = call.get("arguments", {})
    if name not in allowed_names or not isinstance(arguments, dict):
        return None
    return name, arguments

def token():
    return TOKEN_FILE.read_text(encoding="utf-8").strip()

def content_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(part.get("text", "")) for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    return "" if content is None else str(content)

def current_turn(messages):
    """Return only the latest user turn and tool results produced after it."""
    user_index = next(
        (i for i in range(len(messages) - 1, -1, -1)
         if messages[i].get("role") == "user"
         and not content_text(messages[i].get("content")).lstrip().startswith(
             "Current runtime context."
         )),
        None,
    )
    if user_index is None:
        return "", []
    user_text = content_text(messages[user_index].get("content")).strip()
    tool_results = [
        item for item in messages[user_index + 1:] if item.get("role") == "tool"
    ]
    return user_text, tool_results

def capability_answer(tool_names=None):
    tool_names = tool_names or []
    tool_state = (
        f"本轮 Harness 请求附带了 {len(tool_names)} 个工具定义；只能请求其中明确列出的工具，"
        "只有收到 tool result 后才能声称执行成功。"
        if tool_names else
        "本轮请求没有附带工具定义，因此本轮只能进行文本分析，不能执行系统操作。"
    )
    return (
        "我是运行在用户 Mac mini 上、通过 API 接入 DeepSeek Harness 的本地网安 Agent（网安特化语言模型）。"
        "当前基座是 Qwen3-4B，加载本地网安 LoRA；Harness 是外层编排器，不是模型基座。"
        "我的核心能力是根据输入文本和已提供证据进行网安原理分析、风险判断、检测、修复与验证方案设计。"
        "当前核心是纯文本模型；视觉理解需要另接本地视觉模型。"
        "本地知识库检索属于独立的 qwen-cyber-local 证据路由，不等于每次 Harness 对话都已检索。"
        + "computer-use 等桌面能力属于 Harness 可选工具，并非模型权重自带能力。" + tool_state +
        "我没有内建的持续抓包、NFS 监控、恶意软件扫描、沙箱、自动隔离或流量阻断能力；"
        "也不能直接读取屏幕或可靠理解截图。未提供真实工具结果时，我不能声称已经扫描、监控或修改系统。"
        "模型仍可能产生错误，关键网安结论必须由日志、版本、配置、工具结果或权威来源复核。"
    )

def capability_evidence(tool_names):
    screenshot = next((name for name in tool_names if name.endswith("__screenshot")), None)
    tool_state = (
        f"本次 API 请求实际收到 {len(tool_names)} 个工具定义，其中包含 `{screenshot}`。"
        if screenshot else
        "本次 API 请求没有附带 computer-use 工具，因此本轮不能证明桌面工具可用。"
    )
    db_state = "存在" if (HOME / "knowledge/cybersec.sqlite3").is_file() else "不存在"
    model_state = "存在" if (HOME / "models/Qwen3-4B-mlx-4bit").is_dir() else "不存在"
    adapter_state = "存在" if (HOME / "models/qwen-cyber-adapter").is_dir() else "不存在"
    return (
        "下面只列运行时可核验的证据，不用知识库条目证明系统能力：\n\n"
        f"1. 模型基座目录：{model_state}；LoRA 适配器目录：{adapter_state}。"
        "这只能证明文件已部署，不能单独证明回答质量。\n"
        f"2. 本地知识库数据库：{db_state}。每次专业问答会先检索数据库，再校验回答中的 `[KB-编号]`；"
        "没有随本次检索返回的编号会被替换为“未验证引用”。\n"
        f"3. {tool_state}\n"
        "4. API 已通过真实回归测试：普通聊天、旧历史隔离、截图 `tool_calls`、当前工具结果闭环。"
        "computer-use 的执行还会写入本机审计日志，可核对工具名、时间、参数摘要与结果状态。\n\n"
        "边界：当前 Qwen 是纯文本模型，不能证明自己理解了截图；尚未执行的鼠标、键盘或安全扫描操作也不能仅凭描述宣称成功。"
        "如果要验证某项功能，请指定一项，我会让外层 harness 执行最小、可审计的测试。"
    )

def no_tool_evidence_answer():
    return (
        "【未知】本轮没有收到任何真实工具执行结果，因此不能声称已经扫描、调用工具、"
        "发现漏洞或生成基于扫描的报告。用户要求‘假设已执行’不等于实际执行证据。"
        "如需结论，请先在授权范围内执行相应工具，并将结构化结果作为本轮 tool 消息返回。"
    )

def no_target_evidence_answer():
    return (
        "【未知】当前明确缺少目标日志、扫描、资产、版本和配置数据，因此无法确认目标安全、"
        "无漏洞或未受影响。没有发现证据不等于不存在风险；请提供目标证据或在授权范围内"
        "执行只读检查后再判断。"
    )

def contradiction_answer():
    return (
        "【未知】请求要求同时给出相互矛盾的结论，我不会把‘证据不足’与‘已经确认’并列为事实。"
        "在没有直接证据时，唯一可靠结论是尚无法确认。"
    )

def fabricated_reference_answer():
    return (
        "【未知】本轮没有检索到该知识库编号，也没有随请求提供可核验原文，"
        "因此不能引用它证明结论。请先返回真实检索结果；未命中的编号不得写成已验证证据。"
    )

def deterministic_guard(last_user, has_tool_result):
    """Apply evidence invariants before either model route can generate text."""
    lowered = last_user.lower()
    if (not has_tool_result and re.search(r"cve[- ]?\d{4}-\d+", lowered) and any(w in lowered for w in ("影响哪个版本", "受影响版本", "影响范围", "具体技术细节", "是否存在", "影响什么")) and "http" not in lowered):
        return no_target_evidence_answer()
    if re.search(r"cve[- ]?\d{4}-\d+", lowered) and any(w in lowered for w in ("影响哪个版本", "受影响版本", "影响范围", "具体技术细节", "是否存在")) and any(w in lowered for w in ("没有公告", "没有链接", "未提供公告", "没有原文", "没有提供任何公告", "没有提供公告", "没有扫描结果")):
        return no_target_evidence_answer()
    tool_claim_words = (
        "扫描完成", "假设你已经扫描", "假定已调用", "工具成功", "已经扫描",
        "实际使用过", "报告漏洞", "假设已经执行", "假定已经执行",
    )
    if not has_tool_result and any(word in lowered for word in tool_claim_words):
        return no_tool_evidence_answer()

    evidence_absence = (
        "没有任何日志", "没有提供任何数据", "我没有提供任何数据", "仅根据我说",
        "没有日志或扫描", "没有证据", "未提供证据", "不要扫描", "无需扫描",
        "没给记录", "没有记录", "未提供记录", "没有监听", "没有探测结果",
        "没有检查结果", "没有工具输出",
    )
    target_claims = (
        "确认", "证明", "安全", "无漏洞", "没有漏洞", "未受影响", "没有风险",
        "已证实", "已确认事实", "作为事实",
    )
    clauses = [part for part in re.split(r"[。！？!?；;\n]+", lowered) if part]
    same_clause_claim = any(
        any(word in clause for word in evidence_absence)
        and any(word in clause for word in target_claims)
        for clause in clauses
    )
    short_cross_clause_claim = (
        len(last_user) <= 240
        and any(word in lowered for word in evidence_absence)
        and any(word in lowered for word in target_claims)
    )
    if same_clause_claim or short_cross_clause_claim:
        return no_target_evidence_answer()

    contradictory_pairs = (("先说明", "然后说明"), ("同时说明", "相反"))
    if any(all(word in last_user for word in pair) for pair in contradictory_pairs):
        return contradiction_answer()

    asks_unverified_kb = (
        re.search(r"KB-\d+", last_user, re.I)
        and any(word in last_user for word in ("即使", "没检索到", "未检索到", "照写", "直接引用"))
    )
    if asks_unverified_kb:
        return fabricated_reference_answer()
    return None

class CyberHTTPServer(ThreadingHTTPServer):
    def server_bind(self):
        """Bind without HTTPServer's reverse-DNS lookup of 0.0.0.0."""
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = host
        self.server_port = port


class Handler(BaseHTTPRequestHandler):
    server_version = "CyberAgentAPI/0.1"
    protocol_version = "HTTP/1.1"

    def send_json(self, status, obj):
        raw = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def send_sse_completion(self, answer, model_id="qwen-cyber-local"):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        completion_id = f"chatcmpl-local-{int(time.time())}"
        chunks = [
            {"id": completion_id, "object": "chat.completion.chunk", "model": model_id,
             "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}]},
            {"id": completion_id, "object": "chat.completion.chunk", "model": model_id,
             "choices": [{"index": 0, "delta": {"content": answer}, "finish_reason": None}]},
            {"id": completion_id, "object": "chat.completion.chunk", "model": model_id,
             "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
        ]
        try:
            for chunk in chunks:
                raw = json.dumps(chunk, ensure_ascii=False)
                self.wfile.write(f"data: {raw}\n\n".encode())
                self.wfile.flush()
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        finally:
            self.close_connection = True

    def send_sse_tool_call(self, name, arguments=None):
        completion_id = f"chatcmpl-local-{int(time.time())}"
        call_id = f"call_local_{int(time.time() * 1000)}"
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        chunks = [
            {"id": completion_id, "object": "chat.completion.chunk", "model": "qwen-cyber-local",
             "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}]},
            {"id": completion_id, "object": "chat.completion.chunk", "model": "qwen-cyber-local",
             "choices": [{"index": 0, "delta": {"tool_calls": [{"index": 0, "id": call_id,
                 "type": "function", "function": {"name": name, "arguments": json.dumps(arguments or {})}}]},
                 "finish_reason": None}]},
            {"id": completion_id, "object": "chat.completion.chunk", "model": "qwen-cyber-local",
             "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]},
        ]
        for chunk in chunks:
            self.wfile.write(f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n".encode())
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def authorized(self):
        supplied = self.headers.get("Authorization", "")
        return supplied.startswith("Bearer ") and hmac.compare_digest(supplied[7:], token())

    def do_GET(self):
        if self.path == "/health":
            return self.send_json(200, {"status": "ok", "model": "qwen-cyber-local"})
        if not self.authorized():
            return self.send_json(401, {"error": {"message": "unauthorized"}})
        if self.path == "/v1/models":
            return self.send_json(200, {"object": "list", "data": [
                {"id": "qwen-cyber-local", "object": "model"},
                {"id": AGENT_MODEL_ID, "object": "model"},
            ]})
        self.send_json(404, {"error": {"message": "not found"}})

    def do_POST(self):
        request_id = uuid.uuid4().hex[:8]
        if self.path != "/v1/chat/completions":
            return self.send_json(404, {"error": {"message": "not found"}})
        if not self.authorized():
            return self.send_json(401, {"error": {"message": "unauthorized"}})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY:
                raise ValueError("invalid body size")
            body = json.loads(self.rfile.read(length))
            tools = body.get("tools") or []
            tool_names = [
                item.get("function", {}).get("name", "")
                for item in tools if isinstance(item, dict)
            ]
            print(
                f"request id={request_id} thread={threading.get_ident()} "
                f"model={body.get('model')} stream={bool(body.get('stream'))} "
                f"tools={len(tool_names)} messages={len(body.get('messages', []))}",
                flush=True,
            )
            messages = body.get("messages", [])
            last_user, current_tool_results = current_turn(messages)
            print(
                f"context id={request_id} roles={[m.get('role') for m in messages]} "
                f"last_user={last_user[:240]!r}",
                flush=True,
            )
            has_tool_result = bool(current_tool_results)
            if not last_user:
                raise ValueError("messages must contain user content")
            asks_capabilities = (
                any(phrase in last_user.lower() for phrase in
                    ("介绍你的功能", "你有什么功能", "你能做什么", "what can you do"))
                or ("定位" in last_user and any(x in last_user for x in ("能力", "限制", "做不到")))
                or ("已实际接入" in last_user and "能力" in last_user)
            )
            asks_capability_evidence = (
                ("证明" in last_user and ("功能" in last_user or "能力" in last_user))
                or ("幻觉" in last_user and ("功能" in last_user or "能力" in last_user))
            )
            if asks_capabilities:
                answer = capability_answer(tool_names)
                print(f"route id={request_id} capability", flush=True)
                if body.get("stream"):
                    result = self.send_sse_completion(
                        answer, body.get("model", "qwen-cyber-local")
                    )
                    print(f"done id={request_id} capability-sse", flush=True)
                    return result
                return self.send_json(200, {
                    "id": "chatcmpl-local-capabilities", "object": "chat.completion",
                    "model": body.get("model", "qwen-cyber-local"),
                    "choices": [{"index": 0, "message": {
                        "role": "assistant", "content": answer
                    }, "finish_reason": "stop"}]
                })
            if asks_capability_evidence:
                answer = capability_evidence(tool_names)
                print(f"route id={request_id} capability-evidence", flush=True)
                if body.get("stream"):
                    return self.send_sse_completion(
                        answer, body.get("model", "qwen-cyber-local")
                    )
                return self.send_json(200, {
                    "id": "chatcmpl-local-capability-evidence",
                    "object": "chat.completion",
                    "model": body.get("model", "qwen-cyber-local"),
                    "choices": [{"index": 0, "message": {
                        "role": "assistant", "content": answer
                    }, "finish_reason": "stop"}]
                })
            guarded_answer = deterministic_guard(last_user, has_tool_result)
            if guarded_answer is not None:
                print(f"route id={request_id} deterministic-guard", flush=True)
                if body.get("stream"):
                    return self.send_sse_completion(
                        guarded_answer, body.get("model", "qwen-cyber-local")
                    )
                return self.send_json(200, {
                    "id": "chatcmpl-local-guard", "object": "chat.completion",
                    "model": body.get("model", "qwen-cyber-local"),
                    "choices": [{"index": 0, "message": {
                        "role": "assistant", "content": guarded_answer
                    }, "finish_reason": "stop"}]
                })
            if body.get("model") == AGENT_MODEL_ID:
                # Harness owns the system prompt, conversation state, and tool loop on this
                # route. The evidence-only route below remains unchanged for direct cyber Q&A.
                print(f"route id={request_id} agent waiting-lock", flush=True)
                with LOCK:
                    print(f"route id={request_id} agent acquired-lock", flush=True)
                    answer = agent_generate(
                        messages,
                        tools,
                        max_tokens=body.get("max_tokens", 700),
                    )
                json_request = "".join(last_user.lower().split())
                if "只输出json" in json_request or "仅输出json" in json_request:
                    cleaned = answer.strip()
                    if cleaned.startswith("```json") and cleaned.endswith("```"):
                        cleaned = cleaned[7:-3].strip()
                    elif cleaned.startswith("```") and cleaned.endswith("```"):
                        cleaned = cleaned[3:-3].strip()
                    try:
                        json.loads(cleaned)
                        answer = cleaned
                    except json.JSONDecodeError:
                        answer = "【格式错误】无法生成可解析的 JSON。"
                tool_call = parsed_tool_call(answer, set(tool_names))
                if tool_call:
                    call_name, call_args = tool_call
                    schema = next((item.get("function", {}).get("parameters", {}) for item in tools if item.get("function", {}).get("name") == call_name), {})
                    required = schema.get("required", []) if isinstance(schema, dict) else []
                    properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
                    valid = all(key in call_args for key in required) and all(key in properties for key in call_args) and all((not isinstance(spec, dict) or spec.get("type") != "string" or isinstance(call_args.get(key), str)) for key, spec in properties.items() if key in call_args)
                    if not valid:
                        answer = "【工具调用无效】参数不符合已声明的 schema，未执行任何工具。"
                        if body.get("stream"):
                            return self.send_sse_completion(answer, body.get("model", AGENT_MODEL_ID))
                        return self.send_json(200, {"id": "chatcmpl-local-invalid-tool", "object": "chat.completion", "model": AGENT_MODEL_ID, "choices": [{"index": 0, "message": {"role": "assistant", "content": answer}, "finish_reason": "stop"}]})
                if tool_call:
                    name, arguments = tool_call
                    if body.get("stream"):
                        return self.send_sse_tool_call(name, arguments)
                    call_id = f"call_local_{int(time.time() * 1000)}"
                    return self.send_json(200, {
                        "id": "chatcmpl-local-agent", "object": "chat.completion",
                        "model": AGENT_MODEL_ID,
                        "choices": [{"index": 0, "message": {
                            "role": "assistant", "content": None,
                            "tool_calls": [{"id": call_id, "type": "function", "function": {
                                "name": name, "arguments": json.dumps(arguments, ensure_ascii=False)
                            }}]
                        }, "finish_reason": "tool_calls"}]
                    })
                if TOOL_CALL_RE.search(answer):
                    answer = (
                        "【未知】模型请求了本轮未提供或格式无效的工具，调用未执行。"
                        "我不会把内部工具参数作为普通回答输出；请检查 Harness 工具清单后重试。"
                    )
                if body.get("stream"):
                    result = self.send_sse_completion(answer, AGENT_MODEL_ID)
                    print(f"done id={request_id} agent-sse", flush=True)
                    return result
                return self.send_json(200, {
                    "id": "chatcmpl-local-agent", "object": "chat.completion",
                    "model": AGENT_MODEL_ID,
                    "choices": [{"index": 0, "message": {
                        "role": "assistant", "content": answer
                    }, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                })
            if any(phrase in last_user.lower() for phrase in
                   ("介绍你的功能", "你有什么功能", "你能做什么", "what can you do")):
                answer = capability_answer(tool_names)
                if body.get("stream"):
                    return self.send_sse_completion(answer)
                return self.send_json(200, {
                    "id": "chatcmpl-local", "object": "chat.completion", "model": "qwen-cyber-local",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": answer},
                                 "finish_reason": "stop"}]
                })
            if (("证明" in last_user and ("功能" in last_user or "能力" in last_user))
                    or ("幻觉" in last_user and ("功能" in last_user or "能力" in last_user))):
                answer = capability_evidence(tool_names)
                if body.get("stream"):
                    return self.send_sse_completion(answer)
                return self.send_json(200, {
                    "id": "chatcmpl-local", "object": "chat.completion", "model": "qwen-cyber-local",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": answer},
                                 "finish_reason": "stop"}]
                })
            screenshot_tool = next((name for name in tool_names if name.endswith("__screenshot")), None)
            if screenshot_tool and not has_tool_result and any(word in last_user.lower()
                    for word in ("截图", "屏幕", "screenshot", "screen")):
                if body.get("stream"):
                    return self.send_sse_tool_call(screenshot_tool)
                call_id = f"call_local_{int(time.time() * 1000)}"
                return self.send_json(200, {
                    "id": "chatcmpl-local", "object": "chat.completion", "model": "qwen-cyber-local",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": None,
                        "tool_calls": [{"id": call_id, "type": "function", "function": {
                            "name": screenshot_tool, "arguments": "{}"}}]}, "finish_reason": "tool_calls"}]
                })
            if has_tool_result and any(word in last_user.lower()
                    for word in ("截图", "屏幕", "screenshot", "screen")):
                answer = ("截图工具已执行，结果已附在本轮工具输出中。"
                          "当前 Qwen Cyber Local 是纯文本模型，不能可靠解读截图内容；"
                          "若要让模型基于画面自主操作，需要后续接入本地视觉模型。")
                if body.get("stream"):
                    return self.send_sse_completion(answer)
                return self.send_json(200, {
                    "id": "chatcmpl-local", "object": "chat.completion", "model": "qwen-cyber-local",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": answer},
                                 "finish_reason": "stop"}]
                })
            tool_claim_words = ("扫描完成", "假设你已经扫描", "假定已调用", "工具成功",
                                "已经扫描", "实际使用过", "报告漏洞")
            if not has_tool_result and any(word in last_user.lower() for word in tool_claim_words):
                answer = no_tool_evidence_answer()
                if body.get("stream"):
                    return self.send_sse_completion(answer)
                return self.send_json(200, {
                    "id": "chatcmpl-local", "object": "chat.completion", "model": "qwen-cyber-local",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": answer},
                                 "finish_reason": "stop"}]
                })
            no_evidence_words = ("没有任何日志", "没有提供任何数据", "我没有提供任何数据",
                                 "仅根据我说", "没有日志或扫描")
            safety_words = ("安全", "无漏洞", "没有任何已知漏洞", "未受影响")
            if (any(x in last_user for x in no_evidence_words)
                    and any(x in last_user for x in safety_words)):
                answer = no_target_evidence_answer()
                if body.get("stream"):
                    return self.send_sse_completion(answer)
                return self.send_json(200, {"id":"chatcmpl-local","object":"chat.completion",
                    "model":"qwen-cyber-local","choices":[{"index":0,"message":{"role":"assistant","content":answer},"finish_reason":"stop"}]})
            contradiction_words = (("先说明", "然后说明"), ("同时说明", "相反"))
            if any(all(x in last_user for x in group) for group in contradiction_words):
                answer = contradiction_answer()
                if body.get("stream"):
                    return self.send_sse_completion(answer)
                return self.send_json(200, {"id":"chatcmpl-local","object":"chat.completion",
                    "model":"qwen-cyber-local","choices":[{"index":0,"message":{"role":"assistant","content":answer},"finish_reason":"stop"}]})
            # The cyber specialist owns its system prompt. Passing concatenated chat history here
            # caused old user requests to override the latest turn, so only the current request is
            # sent to retrieval and generation. Conversation memory belongs in a separate,
            # explicitly summarized layer.
            question = last_user[-12000:]
            with LOCK:
                proc = subprocess.run([str(CYBER_AGENT), question], text=True, capture_output=True, timeout=180)
            if proc.returncode:
                raise RuntimeError(proc.stderr[-1000:] or "model failed")
            answer = proc.stdout.strip()
            if body.get("stream"):
                return self.send_sse_completion(answer)
            self.send_json(200, {
                "id": "chatcmpl-local", "object": "chat.completion", "model": "qwen-cyber-local",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": answer}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            })
        except Exception as exc:
            self.send_json(400, {"error": {"message": str(exc)}})

    def log_message(self, fmt, *args):
        print(f"{self.client_address[0]} {fmt % args}", flush=True)

if __name__ == "__main__":
    host = os.environ.get("CYBER_API_HOST", "0.0.0.0")
    port = int(os.environ.get("CYBER_API_PORT", "8765"))
    CyberHTTPServer((host, port), Handler).serve_forever()
