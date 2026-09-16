# Strict JSON normalizer — 2026-09-16

The canary API now removes Markdown code fences for explicit JSON-only
requests and validates the result with a JSON parser. A previously fenced
response was returned as raw parseable JSON. Invalid JSON is converted to a
format-error response rather than forwarded. Production was not restarted.
