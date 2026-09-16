# Phase 47 candidate canary

- Candidate base: `Qwen3-4B-mlx-4bit-phase3-wrapper`
- Candidate adapter: `phase37-instruction-repair-20260916`
- Endpoint: `18766` (isolated; production `18765` unchanged)
- Suite: phase35 canary gate, 8 cases
- Result: **8/8 passed**, all responses non-empty
- Covered: identity, general knowledge, defensive security, strict allow/block format, unsupported CVE evidence, tool-claim honesty, evidence boundary, JSON format.
- Production was not switched. Candidate API was stopped after the test.

This is a canary result, not final deployment approval; broader held-out and multi-turn evaluation remains required.
