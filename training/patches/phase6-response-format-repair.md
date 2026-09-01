# Phase 6 response formatting and tool-routing repair

Date: 2026-09-01

## Problem

DeepSeek Harness exposed three integration failures in a long analytical turn:

1. An analytical request received the full Harness tool list, so the model tried
   to place a long report inside `exit_plan_mode` arguments.
2. Generation ended before the JSON tool call closed; the API then leaked raw
   `<tool_call>` markup and returned an incomplete answer.
3. The next plain-text attempt drifted into a learned repair-report template and
   invented source files, line numbers, deadlines, percentages, and run results.

## Deployed repair

- `/Users/jiehan/cyber-agent/api_server_identity.py`
  - SHA-256: `aaffec0ef053b895371e5466d2bfbfc16b1554a42cafe0f76eb174169df29aa5`
- `/Users/jiehan/cyber-agent/mlx_agent_worker.py`
  - SHA-256: `c6a87d421cd35ad564aa6de6b5f11248355aebd9fc34ffa16bf2b1f0d439f019`
- Active model: `/Users/jiehan/models/Qwen3-4B-mlx-4bit-phase3-wrapper`
- Active adapter: `/Users/jiehan/models/qwen-cyber-adapter-phase6-best60`
- Temporary API: `*:18766`, verified listener PID `81749` at the end of the run.

Pre-repair backups remain at:

- `/Users/jiehan/cyber-agent/api_server_identity.py.backup-pre-format-fix-20260901`
- `/Users/jiehan/cyber-agent/mlx_agent_worker.py.backup-pre-format-fix-20260901`

## Changes

1. Tool definitions are passed to the 4B model only for a direct action request.
   Ordinary analysis receives no tools, preventing planning tools from becoming
   an accidental answer channel.
2. Malformed or truncated tool markup triggers a clean Markdown retry with tools
   disabled; raw tool markup is never returned as normal prose.
3. Long structured requests receive a larger token budget.
4. The worker prompt now requires conclusion-first Markdown, full requested
   sections, concise length, and explicit unknowns instead of invented evidence.
5. A second validator rejects obvious section drift and unsupported concrete
   evidence. If both normal generation and corrective generation fail, the API
   returns an explicit evidence-bounded diagnostic instead of the hallucinated
   text.
6. The execution-evidence gate evaluates one sentence at a time and requires a
   real disclosure request. Merely discussing somebody else's execution claim no
   longer triggers the canned gate response.

## Direct API regression

All cases used the OpenAI-compatible `qwen-cyber-agent` route:

- Five-part analytical response: complete A–E Markdown; no tool call, raw markup,
  invented file/line/CVE/percentage, or truncated ending was exposed.
- Cross-sentence discussion of an alleged tool run: substantive analysis, not
  evidence-gated.
- Direct request to list previously successful tools without tool results:
  correctly evidence-gated.
- Explicit read-only screenshot request with a simulated tool definition:
  standard OpenAI `tool_calls` response for `computer__screenshot`.

## Important negative result

The adapter failed both its first generation and its corrective generation on
the long five-part diagnostic. The API validator prevented the bad answer from
reaching Harness, but this is containment, not proof that Phase 6 learned better
instruction following. The adapter still needs base-versus-LoRA blind comparison
and data repair. True token streaming is also not implemented; the API sends
heartbeats and then one final content chunk.

## Recovery

Restart the temporary service with explicit environment variables:

```bash
CYBER_API_PORT=18766 \
CYBER_MODEL_PATH=/Users/jiehan/models/Qwen3-4B-mlx-4bit-phase3-wrapper \
CYBER_ADAPTER_PATH=/Users/jiehan/models/qwen-cyber-adapter-phase6-best60 \
/usr/bin/python3 /Users/jiehan/cyber-agent/api_server_identity.py
```

To roll back this repair, restore both `backup-pre-format-fix-20260901` files and
restart the same port. No model weights or adapters were overwritten.
