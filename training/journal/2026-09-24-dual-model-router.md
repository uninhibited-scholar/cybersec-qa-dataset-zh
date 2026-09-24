# Dual-model router smoke test

## Purpose

Provide one isolated OpenAI-compatible endpoint that prefers the queued/running
large-model backend and falls back to a small CPU model when the large backend
is unavailable or times out. This is a test service, not a production change.

## Components

- Large backend placeholder: `BIG_API` (default `127.0.0.1:19000`)
- CPU fallback: Qwen3-1.7B at `SMALL_MODEL_PATH`, port `19001`
- Router: port `19002`, with `X-Model-Route: big` or `small_fallback`
- Existing production API on port `18765` is untouched.

## Validation

Slurm job `44403` runs the fallback path with an intentionally unreachable
large endpoint (`19999`). It must prove that the router returns a valid
OpenAI-compatible response from the CPU model and marks the route as
`small_fallback`. A successful smoke test is routing evidence only; it is not a
capability score for either model.

## Operational rule

The large model should be exposed on `19000` only when its GPU job has started
and its health endpoint is ready. While queued or unhealthy, requests use the
small model. No automatic deployment, permission expansion, or change to the
existing production service is performed by this router.
