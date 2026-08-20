# Phase 3 API evidence gate

## Root cause

`qwen-cyber-agent` entered the Harness generation branch before the existing evidence guards. Requests asking which tools had already run therefore bypassed `no_tool_evidence_answer()` and reached the model, which could echo the instruction or invent a tool result.

## Fix

Run the evidence-status gate before every model-specific route:

```python
if not has_tool_result and asks_for_tool_execution_claim(last_user):
    answer = no_tool_evidence_answer()
    return openai_compatible_response(answer, stream=body.get("stream"))
```

The detector covers past-tense execution claims such as 已连接、成功调用、已调用、执行过哪些、真实工具返回、工具返回结果 and their English equivalents. It must not block a prospective request to call a tool; an actual tool result in the current turn bypasses this gate.

Mac mini backup before deployment:

`~/cyber-agent/api_server_identity.py.backup-before-evidence-gate-20260820`

Active API source:

`~/cyber-agent/api_server_identity.py`
