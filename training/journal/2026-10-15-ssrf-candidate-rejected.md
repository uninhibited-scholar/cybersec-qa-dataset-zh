# SSRF-focused candidate rejection — 2026-10-15

An isolated worker variant injected the defensive SSRF checklist as an extra
system message. The experiment was stopped after the first cases showed that
knowledge injection alone weakened existing invariants: the fake-CVE response
made an unsupported external-database claim, and the tool-provenance case
returned an uninformative bare “无”。

The variant was not committed, not deployed and not used to alter the
production worker. The result confirms that the next repair must compose SSRF
coverage with the existing evidence and tool policy guards, followed by the
full 12-case blind suite.
