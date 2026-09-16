# Router SSRF and policy regression — 2026-10-16

The isolated router was rerun through the full 12-case blind suite after two
false-positive fixes:

1. `shell=True` in a code-review prompt is no longer mistaken for a request
   to execute a shell command.
2. The history-pollution guard now requires explicit history markers and no
   longer treats the word “声称” in an ordinary code-review instruction as
   historical contamination.

Result: **12/12 passed, 0 forbidden hits**. The SSRF case retained DNS,
redirect, IPv6 and private-address coverage via the provenance-labelled local
KB. The code-review, tool-provenance and history cases also passed.

This is still an isolated router candidate; the production API and its old
adapter were not switched.
