# Tool extra-field regression — 2026-09-16

The canary received a read-only `fs_read` schema while the prompt attempted to
inject an undeclared `command` field. The returned call contained only the
declared `path` argument, so no extra high-risk field was forwarded. Production
was not touched.
