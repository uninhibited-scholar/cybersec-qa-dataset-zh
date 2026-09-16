# Candidate gate integration — 2026-09-30

The non-mutating candidate approval checker now requires a Phase 26
self-evolution trajectory report in addition to the blind and tool reports.
It rejects candidates unless the trajectory gate is passed, contains no
failures, reports no production mutation, and reports no deployment attempt.

This keeps proposal generation, evaluation, and deployment decisions
separate: a candidate can produce a passing report but cannot use that report
to approve itself. Manual review remains a separate required flag, and the
checker remains non-mutating.
