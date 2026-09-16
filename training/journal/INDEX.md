# Training and evaluation index

## Current status

- Production: Qwen base + `qwen-cyber-adapter`; healthy, unchanged.
- Current isolated candidate: `phase33-refine-20260916`.
- Deployment decision: `training/eval/phase31-deployment-decision-20260916.md`.

## Recent evidence

- Phase 31 training and core regression: `2026-09-16-phase31.md`.
- Phase 32 rejected after short-answer regression: `2026-09-16-phase32.md`.
- Phase 33 training and core regression: `2026-09-16-phase33.md`.
- Phase 33 expanded blind evaluation: `phase33-expanded-eval-20260916.json`.
- Phase 33 quality gate: `phase33-expanded-quality-20260916.json`.
- Combined safety/deployment gate regression: `2026-09-16-gate-regression.md`.

## Invariants

Candidates are written to new directories, production is never mutated by training, and self-evolution proposals require independent evaluation plus human approval before deployment.
