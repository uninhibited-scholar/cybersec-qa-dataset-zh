# Training and evaluation index

## Current status

- Production (last verified 2026-09-19): Qwen3-4B phase3-wrapper base + `phase99-multiturn-candidate`; Mac mini API healthy on port 18765, unchanged.
- Current evaluation track: Phase 107, with a local-only 320-case candidate suite (40 × 8 strata), separate answer keys, and two reference runtimes smoke-tested on the school A100 cluster.
- Phase 107 rubric and matched inference protocol remain drafts; no Phase 107 prompt has been sent or scored. Do not use the suite until both are explicitly approved/frozen.
- No Phase 107 training candidate exists yet. Historical Phase 31/33 candidate records remain archived below and are not the current evaluation target.

## Recent evidence

- Phase 107 runtime readiness: `2026-09-19-phase107-runtime-readiness.md`.
- Phase 107 static integrity recheck: `2026-09-19-phase107-static-recheck.md`.
- Phase 107 suite audit: `training/eval/phase107-private-suite-audit.md`.
- Phase 107 scoring rubric draft: `training/eval/phase107-rubric-v0.1-draft.md`.
- Phase 107 inference protocol draft: `training/eval/phase107-inference-protocol-v0.1-draft.md`.
- Phase 31 training and core regression: `2026-09-16-phase31.md`.
- Phase 32 rejected after short-answer regression: `2026-09-16-phase32.md`.
- Phase 33 training and core regression: `2026-09-16-phase33.md`.
- Phase 33 expanded blind evaluation: `phase33-expanded-eval-20260916.json`.
- Phase 33 quality gate: `phase33-expanded-quality-20260916.json`.
- Combined safety/deployment gate regression: `2026-09-16-gate-regression.md`.

## Invariants

Candidates are written to new directories, production is never mutated by training, and self-evolution proposals require independent evaluation plus human approval before deployment.
