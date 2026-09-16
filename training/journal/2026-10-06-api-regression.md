# Production API regression — 2026-10-06

Read-only checks against the live Mac mini service confirmed:

- `/health` returns HTTP 200 and identifies `qwen-cyber-local`;
- `/v1/chat/completions` rejects a request without its bearer credential with
  HTTP 401, so the endpoint is not anonymously callable;
- the service is bound on port `18765` and remains the original production
  process; no candidate adapter was selected or modified.

The authenticated completion path was not exercised because no credential
was read or exposed during this check.
