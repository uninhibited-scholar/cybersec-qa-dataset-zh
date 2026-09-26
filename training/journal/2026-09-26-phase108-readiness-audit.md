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
