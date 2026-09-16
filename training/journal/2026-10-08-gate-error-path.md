# Gate error-path hardening — 2026-10-08

Approval now converts missing or malformed reports and manifests into an
explicit ineligible decision instead of an uncaught exception. The manifest
verification path also computes its error list once, making the result
deterministic and auditable.

Regression check with all report paths missing exited with code 2 and a
structured rejection containing `gate report unreadable`; no files or
production state were changed.
