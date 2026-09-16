# Phase 26 — self-evolution proposal gate

## What changed

Added `training/eval/phase26_self_evolution_gate.py`, an offline and
non-mutating evaluator for candidate trajectory data. It requires provenance
fields (trajectory id, timestamp, model version, source, evaluator version,
reward, and tool events), detects replay contamination, unreviewed
self-generated data, unproven tool results, privilege-expanding actions and
self-approval, and flags suspicious constant-reward runs.

## Verification

The committed two-record fixture passed with `mean_reward=0.9` and
`production_mutated=false`. The evaluator only writes an optional report and
never modifies weights, the production adapter, permissions, or deployment
state.

## Gate policy

This is a proposal-quality gate, not an approval mechanism. A passing report
still requires the existing independent blind tests and manual review before
any candidate can be considered for deployment. Self-evolution code cannot
approve itself or expand tool permissions.
