# 2026-09-27 — tool-permission and provenance gate

The router was tested with screenshot, shell, and web-search tool schemas but
without any tool result messages. Before the guard, the adapter invented a
shell return code and claimed an NVD lookup. A hard provenance gate now returns
one explicit statement that no tool was executed whenever a tool/lookup request
has no `tool` or `function` result message.

Negative tests now pass for screen access, shell execution, and NVD lookup.
Positive tests with explicit tool-result messages remain answerable and are
limited to the supplied result. The gate is isolated in the router; production
API and permissions were not changed.
