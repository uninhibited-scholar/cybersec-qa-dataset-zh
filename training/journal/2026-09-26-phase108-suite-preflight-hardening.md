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

## Read-only cluster status

On 2026-09-26, SSH verification returned host `slurmc` and user `zj225`. No
Phase108 training or evaluation job was pending/running; the only job returned
by `squeue -u zj225` was unrelated `arc2-soar-probe` (PENDING, resources).
`/data3` usage was 280G / 479G (58.5%). No cluster files, jobs, model services,
production configuration, or permissions were changed.

## Draft-builder integration audit

Read-only inspection of the uncommitted v0.3 source builder/test found that
`build_phase108_private_source.py` emits no `scenario_root_id`; its test only
checks that `scenario_family` strings are unique, but those strings are
constructed from category and row index and therefore do not establish
independent roots. The stricter preflight consequently cannot accept this
builder's output, as intended. The v0.3 draft already has a separate rejection
record for semantic near-duplicates. Do not patch it with per-row IDs: a
replacement authoring pipeline must derive root identity from the underlying
scenario and fail when the same scenario is reused across categories.
