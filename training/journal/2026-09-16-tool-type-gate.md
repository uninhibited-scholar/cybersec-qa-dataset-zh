# Tool type validation — 2026-09-16

Canary testing found that a declared string parameter could previously be
returned as a number. The API schema gate now validates string property types
before forwarding a call. A numeric `path` request was rejected with no tool
execution. Production remained untouched.
