# Phase108 test-split preservation and parent-hash correction — 2026-09-26

## Authoritative recheck

- Cluster: `slurmc`, account `zj225`; no active jobs at the time of check.
- `/data3` quota: 280G / 479G (58.5%).
- Reserved `phase108-clean-v2/test.jsonl` SHA-256:
  `ddf38609d85f5105622ed86c694affa793423df2371f6d20d2fe4bf9399b86ee`.
- Parent adapter SHA-256, confirmed by direct remote `sha256sum` and candidate
  manifest:
  `3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`.
- Corrected-r2 candidate SHA-256:
  `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`.
- No one-time test-loss result file exists; this check did not read or tokenize
  the reserved test split.

## Decision

Do not consume the reserved test split for a parent-vs-candidate loss comparison
at this point. The candidate already had a functional failure on the exposed
v0.9 diagnostic sample (16/16 empty generations for both parent and candidate,
as recorded in the Phase108 scale-provenance audit). A test-split loss number
cannot resolve that generation/runtime failure and is not a blind capability
evaluation. Preserve the test split until a preregistered, useful final check is
defined; do not use its result for checkpoint selection.

## Correction

An unsubmitted, unexecuted draft diagnostic runner contained a parent-hash
transcription typo (`...1498332...`). The authoritative hash is
`...14198332...`, consistently recorded by the cluster file, candidate
manifest, and prior provenance logs. The flawed draft runner and its Slurm
wrapper were removed before submission. No model, adapter, validation data,
production service, scoring rule, or tool permission was changed.

## Remaining gate

Phase108 has a verified scale-corrected candidate and fixed-validation
comparison, but no valid independent blind behavioral result. Existing v0.3–v0.9
private drafts were rejected for exposure/repetition; they must not be recycled
or cosmetically re-IDed. The independent benchmark gate remains open.
