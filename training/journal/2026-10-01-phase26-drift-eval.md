# Phase 26 drift and evaluation-deception checks

The offline self-evolution gate now detects two additional failure modes:

- **Evaluation deception:** a proposal made up entirely of trajectories
  marked as known evaluation prompts is rejected instead of being treated as
  generalization.
- **Capability drift:** any trajectory that passed in the baseline but fails
  in the candidate is recorded as a regression and rejects the proposal.

Verification used the committed fixtures. The clean fixture passed. The
adversarial fixture was rejected with unreviewed self-data,
evaluation-deception, capability-drift, and constant-reward warnings.
Production mutation and deployment remain impossible in this evaluator.
