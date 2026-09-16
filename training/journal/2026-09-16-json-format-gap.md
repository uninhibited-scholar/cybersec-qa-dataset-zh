# Strict JSON format gap — 2026-09-16

Canary testing asked for JSON-only output with exactly `risk` and `reason`.
The model returned valid JSON semantics but wrapped it in a Markdown code fence.
This is a caller-visible format violation for strict parsers and remains an
open gate item; production was not changed.
