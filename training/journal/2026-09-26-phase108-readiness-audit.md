# Phase108 readiness audit — 2026-09-26

## Scope

Read-only readiness check for the isolated Phase108 candidate workflow. No
production API, production adapter, evaluation rubric/protocol, tool
permissions, candidate weights, or evaluation data were changed.

## Evidence

- CUHK scheduler snapshot at 2026-09-26 18:55 HKT showed jobs `44593`
  (`p108-follow-val`) and `44601` (`qwen14b-api-service`) in `PENDING` with
  reason `Priority`; neither was a running model service.
- The same SSH session reported quota 280G/479G (58.5%).
- Later SSH attempts to the recorded controller address connected to TCP/22
  but were closed during SSH key exchange, before account authentication.
  The cluster's current job state could therefore not be refreshed.
- `training/slurm/phase108_candidate_sandbox_server.sbatch` is a legacy,
  untracked launcher hard-coded to the Phase91-era step-7000 adapter SHA
  `919a9e...a2d3`; it is not a launcher for corrected-r2 SHA
  `4e9177...3772`. Do not use it to serve or evaluate corrected-r2.
- Corrected-r2 and parent showed scale-sensitive empty outputs in prior
  exposed diagnostics. The scale-5 diagnostic produced no empty responses in
  16 cases per arm, but every response hit its 128-token cap; it cannot justify
  selecting scale 5 or making a capability claim.
- Local checks passed with the correct module path:
  `PYTHONPATH=training/scripts python3 -m unittest test_phase108_lora_scale
  test_phase108_scale_candidate_preflight test_phase108_api_function_smoke
  -v` — 6 tests passed. Both fixed-validation Slurm scripts passed `bash -n`,
  and `git diff --check` passed.

## Readiness decision

There is no verified, running Phase108 service on the cluster. The current
candidate is not eligible for production deployment: independent blind-suite
construction/review remains unresolved, and exposed functional diagnostics
are insufficient. The legacy sandbox launcher must not be mistaken for the
corrected-r2 candidate path. Next steps are to restore reliable scheduler
access, finish the pending isolated fixed-validation work, and prepare a
separate hash-pinned candidate sandbox launcher only after the required
candidate/scale is selected. No automatic deployment is authorized.

## Isolated launcher follow-up

Prepared `training/slurm/phase108_corrected_r2_sandbox_smoke.sbatch` as a
separate, non-production launcher pinned to corrected-r2 adapter SHA
`4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`, the
existing sandbox server/loader/smoke-script hashes, the base config/index
hashes, and the training-time scale 20. It binds only through the existing
loopback-only server and records metadata-only smoke results in a unique,
permission-restricted run directory. The smoke checks API health, one benign
non-empty response, and rejection of tool requests; it is explicitly not a
capability score or a promotion gate.

Local `bash -n` and `git diff --check` passed, and all pinned local script
hashes matched. The launcher has **not** been synchronized or submitted:
SSH to the cluster controller currently closes before key exchange, so no
claim is made about its remote copy or runtime. It must be hash-verified on
the cluster before submission.

## Corrected-r2 sandbox smoke — Slurm job 44611

The hash-pinned launcher and uniquely named server/client were synchronized
without overwriting the older remote server. All remote server, loader, smoke
client, launcher, base-config, base-index, and corrected-r2 adapter hashes
matched the expected values before launch. The adapter was re-hashed after
inference and still matched.

Authoritative `sacct` reports job 44611 `COMPLETED`, exit code `0:0`, elapsed
`00:01:02`, node `dell3090`. The metadata-only result reports health HTTP 200,
model discovery HTTP 200, one benign completion HTTP 200 with non-empty text
(54 characters, finish `stop`, scale 20), and tool request HTTP 400 rejected.
The smoke result SHA-256 is
`c220d1b6d49f87971fdb41c3391b8a5d3cd2b96bc08b3e244bc62f5f998fda82`.
The result is archived separately at
`training/journal/phase108-corrected-r2-sandbox-smoke-44611.json`.

This is only a serving-compatibility and one-prompt functional smoke. It does
not assess answer correctness, the known exposed-suite empty-output cases,
general capability, blind-suite performance, or promotion eligibility. The
Slurm allocation ended and no sandbox API process remained. Production
service/adapter, rubric/protocol, permissions, and candidate weights were not
changed.
