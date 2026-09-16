# Candidate manifest and rollback traceability

Added `training/scripts/candidate_manifest.py`. It creates a deterministic
manifest of candidate files, sizes, SHA-256 hashes, model version and an
explicit `production_mutated=false` invariant. The same script can verify a
candidate directory against a saved manifest and reports file-set or hash
changes without modifying the candidate or production adapter.

The script was syntax-checked and exercised against the Phase 26 fixtures;
the output included stable hashes and the production-mutation invariant.
