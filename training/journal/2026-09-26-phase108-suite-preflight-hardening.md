# Phase108 candidate-suite preflight hardening — 2026-09-26

## Change

Hardened `training/scripts/phase108_candidate_suite_preflight.py` to require a
globally unique, author-supplied `scenario_root_id` for every proposed fixture.
The preflight now rejects duplicate roots even when fixtures have different
category labels or fixture IDs. Its report includes the number of distinct
roots and explicitly warns that unique IDs are structural evidence only; they
do not prove semantic independence.

Added regression tests for a scenario root repeated across categories and for a
missing root ID. The test suite passed locally: `4 passed`.

## Scope and limitations

This change prevents a known structural failure mode, but does not itself
repair or certify any existing benchmark. Semantic review, overlap/near-dup
checks, contamination review, source/answer-key separation, and hash freezing
remain required before any blind run. No model inference, validation scoring,
cluster job, production API, adapter, rubric, protocol, or tool permission was
changed.

## Reproducibility

- Test: `python -m pytest -q training/eval/test_phase108_candidate_suite_preflight.py`
- Result: 4 passed.
- `git diff --check`: clean before commit.
