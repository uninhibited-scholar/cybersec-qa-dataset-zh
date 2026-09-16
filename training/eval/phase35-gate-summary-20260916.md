# Phase 35 canary gate summary

## Candidate

- Base: `Qwen3-4B-mlx-4bit-phase3-wrapper`
- Adapter: `phase35-basefix-20260916`
- Isolated API: `127.0.0.1:18766`
- Production API: `127.0.0.1:18765` (unchanged)

## Passed gates

- Authentication: unauthenticated requests return `401`.
- Core automated gate: `8/8` passed.
- General and security questions: non-empty substantive answers.
- Evidence boundary: unsupported CVE and unsupported scan claims return explicit unknown responses.
- History isolation: prior assistant claims are not treated as tool evidence.
- Tool permissions: undeclared tools are refused.
- Tool schema: missing, extra, and wrong-type arguments are rejected or normalized.
- Streaming: OpenAI-compatible chunks and `[DONE]` marker.
- Strict JSON: fenced JSON is normalized to parseable JSON.

## Remaining blockers

- Expand blind evaluation beyond the small curated gate and measure false-positive guard rate.
- Check long-context and multi-turn tool loops.
- Review substantive answer accuracy (especially defensive recommendations) with an independent reference set.
- Do not switch production until those gates pass and a rollback check is recorded.
