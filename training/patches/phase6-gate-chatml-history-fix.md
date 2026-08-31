# Phase 6 gate, ChatML, and history repair

Date: 2026-08-31

## Deployed files

- `/Users/jiehan/cyber-agent/api_server_identity.py`
  - SHA-256: `1d1e14a00298ccf4413d1832b1aa570fc17aa1b9d4f1b96271cb3bc0d0da8df9`
- `/Users/jiehan/cyber-agent/mlx_agent_worker.py`
  - SHA-256: `fd939a47299453b332ffb631b7293aba517c90dd4e1d5c079b57a6b5fd96e96a`

Backups:

- `/Users/jiehan/cyber-agent/api_server_identity.py.backup-pre-gate-chatml-20260831`
- `/Users/jiehan/cyber-agent/mlx_agent_worker.py.backup-pre-gate-chatml-20260831`

## Changes

1. The execution-evidence gate now requires all three categories: an explicit
   completion/past marker, an execution object, and a request to disclose the
   result. Merely discussing missing evidence or saying “do not invent tool
   calls” no longer triggers it.
2. Exact legacy canned gate answers and their immediately preceding user turns
   are removed before sending history to the agent worker. This repairs existing
   conversations without broadly deleting normal history.
3. The worker now serializes messages with Qwen ChatML delimiters instead of the
   ad-hoc `问题：...回答：` wrapper. Harness system/runtime payloads remain omitted,
   while the local identity and tool schema are placed in the ChatML system turn.
4. The HTTP server enables address reuse for predictable local restarts.

## Startup correction

The API does not parse the previously supplied `--port`, `--model`, or
`--adapter` arguments. They were silently ignored. The working temporary launch
uses these environment variables instead:

```bash
CYBER_API_PORT=18766 \
CYBER_MODEL_PATH=/Users/jiehan/models/Qwen3-4B-mlx-4bit-phase3-wrapper \
CYBER_ADAPTER_PATH=/Users/jiehan/models/qwen-cyber-adapter-phase6-best60 \
/usr/bin/python3 /Users/jiehan/cyber-agent/api_server_identity.py
```

## Regression results

- Gate unit cases: 5/5.
- Legitimate missing-evidence analysis: substantive answer, not gated.
- Explicit request to list already-successful tool calls without results: gated.
- Two legacy canned exchanges followed by a normal question: substantive answer.
- Simulated read-only screenshot tool definition: valid OpenAI `tool_calls` reply.
- Fresh Harness turn: substantive known/unknown/validation answer; about 22 s.
- Same Harness conversation follow-up: substantive answer; about 37 s.
- No empty output, canned false refusal, or training-template tail in the two
  repaired Harness turns.

## Remaining limitations

- One answer incorrectly described 502 as a timeout; 502 is Bad Gateway, while
  504 is Gateway Timeout.
- The first direct analysis over-inferred that intermittent behavior excludes
  static code defects; the follow-up correctly rejected that inference.
- Latency remains high and the Harness UI reports zero token throughput because
  the API still emits generated text as one final chunk after heartbeat comments.
- Phase 6 is improved but is not yet approved as a top-quality specialist model.
