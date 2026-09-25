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

## Isolated blind smoke result

- Slurm job `44430` loaded the candidate on a loopback-only sandbox; the server
  reported 28 adapter projections and the pinned candidate SHA.
- The sealed v0.9 case source was sampled inside the job (16 cases; prompts and
  responses were not written to scheduler logs).
- All 16 responses were empty (`chars=0`), with the empty-string SHA repeated
  for every case. This is a deterministic functional failure signal, not a
  capability pass or a minor score regression.
- The candidate is rejected for further deployment consideration. Production
  remains unchanged.

## Follow-up scale diagnostic

Three isolated compatibility probes at inference scales 1, 2.5, and 20 all
produced non-empty output for the standard smoke prompt. Therefore the 16/16
empty responses are not explained by a universal adapter loader or scale
failure; they are specific to the sealed multi-category blind prompts (or a
candidate behavior regression on those prompt forms). This does not rescue the
candidate: the blind functional gate remains failed.
