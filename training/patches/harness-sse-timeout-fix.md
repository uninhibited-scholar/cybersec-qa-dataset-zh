# DeepSeek Harness API SSE timeout fix

Date: 2026-08-31

## Symptom

DeepSeek Harness displayed no answer even though the Mac mini API eventually
logged HTTP 200. A new conversation generated two concurrent requests: a
session-title request without tools and the actual answer request with tools.

## Root cause

- The title request unnecessarily occupied the single MLX worker first.
- The answer route advertised SSE but did not send headers or chunks until the
  full generation had completed.
- Harness timed out at roughly 60 seconds, discarded the late response, and
  retried, leaving more requests queued behind the worker lock.

## Deployed fix

Remote file: `/Users/jiehan/cyber-agent/api_server_identity.py`

Backup: `/Users/jiehan/cyber-agent/api_server_identity.py.backup-before-sse-fix-20260831`

SHA-256 after deployment:
`fd7b3136eeabe01f69a3923eced46f35db359618df9c8a8933e9390cd196db42`

Changes:

1. Detect Harness session-title prompts and generate a deterministic title
   without invoking MLX.
2. Parse the title payload from the first JSON array delimiter rather than the
   first colon in the prompt.
3. For model generation, send SSE headers and an empty assistant chunk
   immediately.
4. Run generation in a worker thread and send an SSE comment heartbeat every
   five seconds while waiting for the serialized MLX worker.
5. Emit the final text or validated tool call and a normal `[DONE]` event.
6. Tolerate clients disconnecting while a generation is still finishing.

## Regression results

- MacBook tunnel health (`127.0.0.1:18764`): OK.
- Title request: HTTP 200, TTFB 0.001735 s, total 0.001969 s, correct title.
- Real model request: HTTP 200, TTFB 0.002478 s, total 11.603657 s.
- Two five-second keep-alive comments were observed before the final answer.
- The final answer and `[DONE]` event arrived successfully.

## Scope and remaining limitation

This fixes the transport/queueing failure that made Harness show no output. It
does not approve the Phase 6 adapter for deployment. The sampled answer still
contained an unwanted training-format tail, so response quality and Phase 6
evidence-boundary failures remain separate model/training issues.

## Recovery

Restore the backup file, restart the service on port 18766, and verify
`/health`. Do not print or commit the bearer token during recovery.
