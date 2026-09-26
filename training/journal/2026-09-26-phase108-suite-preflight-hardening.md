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

## Follow-up: answer-key contract validation

An additional schema audit found that the v0.3 benchmark specification
requires a per-case `format_contract`, but this structural preflight did not
require or validate that field. It also accepted non-string/blank entries in
`must_cover` and `must_not_claim`. The preflight now rejects those omissions
and malformed entries. This does not establish semantic freshness; the
independent review and contamination gates above remain mandatory.

- Regression command: `python3 -m pytest -q training/eval/test_build_phase108_private_source.py training/eval/test_phase108_candidate_suite_preflight.py training/scripts/test_phase108_scale_candidate_preflight.py`
- Result: 10 passed.
- `git diff --check`: clean.
- At this follow-up, the cluster hostname did not resolve and the previously
  recorded controller IP closed SSH. No job status or output could be verified;
  no model or evaluation job was started, and no remote artifact was copied.

## Follow-up: cross-case scenario-fact atom gate — 2026-09-26

Two independent reviewers separately audited the benchmark specification and
the structural preflight design. Both emphasized that globally unique IDs,
scenario-root labels, family labels, or category-specific wording can still
hide a repeated underlying incident. They also identified a multi-turn risk:
reusing a motif in either turn, or reversing a reused pair, does not create a
new independent root. Their reviews did not inspect model outputs or scores.

Added a required `scenario_facts` list to proposed source rows. The preflight
now requires at least two nonblank fact atoms per case and rejects exact
normalized atom reuse both within a case and across the full suite, including
across categories. Its aggregate report records the number of unique atoms.
The rejected v0.3 builder test now explicitly proves that fake category-level
diversity cannot hide its 40 reused incident motifs from this gate.

This is a narrow exact-atom screen, not semantic validation: paraphrased or
dishonestly labeled atoms can evade it. A full independent scenario-family
review and lexical/overlap scans remain mandatory; no existing draft becomes
eligible because of this change. No prompts were sent to a model, no evaluation
was scored, and production, adapter weights, rubric, protocol, and permissions
remain unchanged.

- Regression command: `python3 -m pytest -q training/eval/test_phase108_candidate_suite_preflight.py training/eval/test_build_phase108_private_source.py training/scripts/test_phase108_scale_candidate_preflight.py`
- Result: 12 passed (Python 3.14 emitted only the existing Pydantic compatibility warning).
- `git diff --check`: clean.
