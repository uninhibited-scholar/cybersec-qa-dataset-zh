# Tool schema validation — 2026-09-16

Canary testing found that malformed calls could pass the previous parser when
arguments were merely JSON objects. The canary API now checks declared
`required` and `properties` fields before returning a tool call; invalid calls
return a no-execution response. A missing-required-`path` `fs_read` case passed
the new gate. Production was not restarted.
