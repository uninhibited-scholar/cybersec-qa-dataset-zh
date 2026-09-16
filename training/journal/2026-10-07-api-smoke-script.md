# Safe API smoke script — 2026-10-07

Added `training/eval/api_smoke.py`. It reads an API URL and bearer token only
from environment variables, never prints or persists the token, always checks
`/health`, and only sends a harmless ordinary-knowledge prompt when a token
was explicitly supplied. Without a token it skips generation rather than
guessing credentials.

The script was copied to the Mac mini and returned HTTP 200 from the live
health endpoint for `qwen-cyber-local`; no authenticated request was made and
production state was unchanged.
