# Cluster serving recheck — 2026-09-27

## Verified state

- Slurm job `44601` (`qwen14b-api-service`) is currently `RUNNING` on `a100-3`,
  partition `GPU-LARGE`; requested time limit is 2 days. At the recheck it had
  run for about 12h34m.
- This is a bounded, isolated service using the general Qwen3-14B BF16 model
  with a Qwen3-1.7B CPU fallback. The service manifest explicitly says
  `phase108_adapter_loaded=false`; it is not the Phase108 cyber adapter and is
  not a production promotion.
- The job log reports successful health checks, `/v1/models`, and non-empty
  streaming and non-streaming requests through both fallback and large-model
  routes. This is a successful service smoke test, not a capability evaluation.
- Router and model processes bind to compute-node loopback. The job advertises
  a local SSH tunnel via `a100-3`; a live tunnel was attempted from this Mac
  but failed because the existing Ed25519 key was accepted by `slurmc` and
  rejected by `a100-3` (`Permission denied (publickey,password)`). Thus the
  service is healthy inside the allocation but laptop/API reachability is not
  yet verified. No host-key checking was disabled and no credentials were
  changed.
- Separately, Phase108 blind collection job `44803` remains `RUNNING` on
  `titanv1`. Its anonymized alias C has 320/320 responses with 298 empty; alias
  B has 40/320 at this check. The alias map was not inspected, and no arm-level
  interpretation or capability conclusion is made before all arms and
  integrity checks complete.

## Changes and next action

- No production API, adapter, evaluation rubric/protocol, permissions, or
  candidate weights were changed.
- Resolve authorized SSH access to the allocated compute node (or use an
  administrator-approved tunnel mechanism), then verify `/health`,
  `/v1/models`, and one non-empty completion through the laptop tunnel.
- Keep the general Qwen14B service separate from Phase108 evaluation and do not
  describe it as the trained cyber-specialized model.
