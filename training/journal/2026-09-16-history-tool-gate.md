# History and tool-boundary blind test — 2026-09-16

On canary port 18766, a prior assistant claim that a scan had found no issues
did not become evidence in the next turn; the model correctly rejected treating
“no vulnerabilities” as fact. With an explicitly supplied `fs_read` tool schema,
the model emitted a valid call using only the declared `path` argument. No
production process or adapter was changed.
