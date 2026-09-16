# 2026-09-24 — decoupled base/adapter router evaluation

Open-ended regression showed that the small targeted adapters can answer the
exact training prompts while returning empty strings for unrelated ordinary
questions. Since the architecture explicitly keeps the base model and cyber
adapter separate, an isolated router was added for evaluation:

- security-scoped prompts route to the cyber adapter;
- ordinary prompts route to the unchanged base model;
- the same evidence-stop and tool-provenance guard applies after generation;
- no production API or adapter path was changed.

Smoke tests confirmed a Python list/tuple question routes to `base` and gets a
normal answer, while an unsupported CVE question routes to `cyber` and returns
only `无法核验。`. The router is a candidate serving architecture, not yet a
deployment approval; it still needs the complete blind suite, tool-call tests,
and a review of system-prompt leakage.

The expanded 12-case run scored 11/12. The only miss exposed a routing bug:
the SSRF prompt described URL fetching, HTTPS, loopback, and Host headers
without spelling “SSRF”, so it initially went to `base`. The security intent
regex now recognizes those concrete indicators; a direct retest routes the
same prompt to `cyber`. This change is isolated and production remains
unchanged.
