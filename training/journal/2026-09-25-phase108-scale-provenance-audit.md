# Phase108 scale-corrected provenance audit — 2026-09-25

## Scope

This is an isolated audit. It does not modify the production API, production
adapter, evaluation rubric, validation data, or tool permissions.

## Evidence from the CUHK cluster

- Corrected candidate: `phase108-cuda-recovery-scale20-corrected-20260924-r2`
- Candidate adapter SHA-256: `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`
- Input adapter file SHA-256 (direct `sha256sum`):
  `3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`
- Candidate manifest records the same input hash and records rank 8, MLX scale
  20, PEFT alpha 160, and effective scale 20.
- The no-inference preflight passes when supplied the directly observed input
  hash.

## Blocking discrepancy

The previously sealed expected hash was
`3ed1a85e7b021e1498332a525bfa4bb75b336a03579d526f8210f1576317036`, which
differs from the directly observed file hash. The discrepancy is not silently
overridden. It must be reconciled as a provenance-record correction or an
input-artifact mismatch before fixed validation is scheduled.

## Validation status

- Phase108 jobs 43961–43968 failed in the loader before evaluation because the
  old runner rejected MLX adapter keys.
- Jobs 44069–44084 evaluated older candidates, not this corrected-r2 candidate.
- No capability or deployment claim is supported yet for corrected-r2.

