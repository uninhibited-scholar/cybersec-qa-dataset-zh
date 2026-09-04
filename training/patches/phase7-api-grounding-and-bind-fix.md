# Phase 7 API grounding and startup repair

Date: 2026-09-04

## Scope

Remote runtime file: `/Users/jiehan/cyber-agent/api_server_identity.py`.
Deployed SHA-256: `aead5246cf13ab041b1c99db907cb262bd5d9519bbdc00a22ea28040a21e9dfb`.

The repair changed only the API/Harness orchestration layer. It did not modify
base-model or LoRA weights.

## Changes

1. Capability responses now use the stable identity `本地网安 Agent`, identify
   Qwen3-4B and the LoRA separately from DeepSeek Harness, and describe
   `computer-use` as an optional outer tool.
2. Evidence invariants run before both `qwen-cyber-local` and
   `qwen-cyber-agent`, so the Harness model route cannot bypass them.
3. Unsupported target-safety claims, fabricated KB citations, contradictory
   conclusions, untrusted previous-assistant claims, and claims of completed
   actions without tool results return an explicit `【未知】` response.
4. Long prompts use clause/length-bounded matching to avoid the earlier
   cross-sentence keyword-intersection failure.
5. Valid Qwen tool markup is converted to OpenAI `tool_calls`; invalid or
   unavailable tool markup is not exposed as ordinary answer text.
6. `CyberHTTPServer.server_bind` bypasses `HTTPServer`'s reverse-DNS lookup of
   `0.0.0.0`. On the deployed macOS 26.5.2 / Python 3.14 host, that lookup left
   the socket listening while requests timed out until an unrelated signal
   interrupted `gethostbyaddr`.
7. The API now runs as the per-user LaunchAgent
   `com.uninhibited-scholar.cyber-agent-api`, using the tracked plist under
   `training/network/`.
8. The MacBook tunnel now forwards `127.0.0.1:18764` to Mac mini port 18765,
   and `dsh web` has its own tracked KeepAlive LaunchAgent so the browser client
   does not outlive its backend.

## Recovery

The last pre-fix runtime backup is
`/Users/jiehan/cyber-agent/api_server_identity.py.backup-pre-dns-bind-fix-20260904`.
Earlier intermediate backups with the `pre-guard`, `pre-bounded-guard`, and
`pre-selector-fix` suffixes were also retained.

To restart the tracked service:

```bash
launchctl kickstart -k gui/$(id -u)/com.uninhibited-scholar.cyber-agent-api
curl -fsS --max-time 3 http://127.0.0.1:18765/health
```

To inspect the active adapter without printing credentials:

```bash
launchctl print gui/$(id -u)/com.uninhibited-scholar.cyber-agent-api
```
