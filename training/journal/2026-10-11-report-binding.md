# Report-to-candidate binding — 2026-10-11

The approval gate now binds the architecture report to the exact candidate
directory under review. A passing report for another adapter is rejected;
base-model and Harness identities must also be present. This closes a
stale-report substitution path while preserving the non-mutating behavior.
