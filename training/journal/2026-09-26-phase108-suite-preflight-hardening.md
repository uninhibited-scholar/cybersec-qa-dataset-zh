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

## Private evidence-boundary pilot revision — 2026-09-26

Continued the private 40-case evidence-boundary pilot after independent review.
Revised three source/key pairs: corrected the HTTP 200 layer description, and
replaced two backup/attribution-neighbor scenarios with distinct forensic
image-integrity and build-to-runtime provenance cases. Two independent
reviewers rechecked all three revised cases plus the two neighboring cases;
all five passed for factuality, evidence-bounded keys, answerability, and
defensive-only scope. The remaining 35 cases are unchanged from the prior
reviewed draft. No model inference or capability scoring was run.

The regenerated pilot has 40 unique cases, 40 roots, and 80 exact-distinct
scenario fact atoms. The structural preflight correctly remains `fail` because
this is only one of the eight required categories, not a complete benchmark.
The updated lexical audit found no pair above its 0.52 triage threshold. The
local exact-overlap scan covered 366 split/batch JSONL files (21,956 indexed
unique prompts), found zero exact overlaps and zero parse errors, and left 10
unrecognized rows in historical result JSONLs. These are bounded screens, not
semantic or pretraining-contamination certification.

Private raw fixtures, prompts, and answer keys remain gitignored. Their current
SHA-256 values are recorded here for traceability only:

- Source fixtures: `039a74f6b31015b04e6765d9f94fc24b9ef22d0490ce9ebad74e92b60e96886f`
- Prompt manifest: `d330ae25f5a8e8b8a38ee98f540ab69f3518b32e4c81568216fc5ec10c5496c5`
- Answer keys: `9908d8bd42bca791f9d3c2406e0cedd827acd5c2b4a7863e3078d49aa93ef677`
- Preflight report: `acd75055747cecbb14b54b6f09822884fbef031f564c94d526bcdffb68afc24b`
- Near-duplicate report: `0a93d60bf6b31c20e5d2738174e193ae1838b9060a5c2e585117ca0892cafadc`
- Exact-overlap report: `31644c21f659fe2be4b4cbffced530daf551ed7980d7e406d7b975aaebbfe142`

The fixed Phase108 parent validation remains a batch-only validation-loss run,
not a hosted API service; no candidate server or production service was
started, and production API/adapter, rubric, protocol, and permissions remain
unchanged.

## Isolated candidate API function smoke — 2026-09-26

The existing candidate-server draft pointed at a stale step-7000 artifact and
only checked `/health`. Replaced that diagnostic path with a uniquely named,
hash-pinned smoke job for the corrected-r2 final adapter. The server remains
loopback-only, has no tools, writes no weights, uses short-lived per-scale
processes, and the client records metadata only. A regression test verifies
that generated text is never written to the result or printed.

The nominal CPU test partition was not usable for inference: Slurm reports only
one effective CPU and 1 MiB configured memory per node. Rather than run on the
login node or wait several days for the medium queue, a one-hour job was
scheduled on the idle `titanv1` node. The server selected FP16 for its
compute-capability 7.0 GPU; it loaded the pinned corrected-r2 adapter and all
28 LoRA projections, binding only to `127.0.0.1`.

Job `44586` completed `COMPLETED`, exit `0`, in `00:01:51`. For one benign
functional probe at each setting:

- Scale 20: health/models/chat returned HTTP 200, one non-empty 54-character
  response, finish reason `stop`, and a tool-enabled request was rejected with
  HTTP 400. Result metadata SHA-256:
  `ff9496a5b160f15d83eb04c6a94f491393d6993dd3340712261ea9dec77bfb46`.
- Diagnostic scale 5: the same API checks passed, with one non-empty
  51-character response and tool rejection HTTP 400. Result metadata SHA-256:
  `f044992416945c7881a6d7694d82bf6b000731e7212c7674f155b405db6f2254`.

Both runs used adapter SHA-256
`4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`.
Smoke-client SHA-256 is
`b1ac9d684a3e0efa3d445fe67c779fd1fafa73fcc62cc9944a44fcd511b909b2`; server
SHA-256 is
`df1484bd0b01ee72e3b41dbb2a7ceda7b384d1e08f99239ffde68357338f83f7`; job
script SHA-256 is
`68a77c50966418d67c798b5f135183e1bc7548755b29cbc4739a206340cec670`.

This establishes basic API compatibility for a single neutral request on
this compute node, not stable remote availability, response quality, a
selected inference scale, or candidate promotion. In particular, the prior
16/16 immediate-EOS diagnostic on different exposed prompts remains a blocking
functional signal. The temporary API exited with the Slurm job; no persistent
endpoint or SSH tunnel was established. The Phase91 production API/adapter,
rubric, protocol, tool permissions, and candidate weights remain unchanged.

## Paired public API functional screen for Phase108 follow-up candidates — 2026-09-26

To avoid treating the corrected-r2 smoke result as sufficient, ran a matched,
metadata-only functional screen on the formatmix and bare-canary adapters,
with corrected-r2 re-run as a same-job control. Slurm job `44588` was an
initial candidate-only screen; job `44589` ran all three adapters sequentially
on the same NVIDIA TITAN V/FP16 sandbox API at scale 20. Both jobs completed
successfully (`44588`: 00:02:03; `44589`: 00:01:32). Each candidate received
the same four fixed, benign public-development probes; tools were absent and
the explicit tool-request check was rejected with HTTP 400. The HTTP health,
model-list, and four chat requests returned 200 for every candidate.

All three adapters yielded 4/4 non-empty responses on this narrow probe set:

- formatmix: adapter SHA-256
  `3c87564c97b003990242b988c72cd8c76a9ccf0f8bfbf1058a106f53e26ef461`;
  empty count 0; summary SHA-256
  `fcf68691decd38b52bf998f652fb0a0f829acc2463bd5dfa9a59dfcdef9ae197`.
- bare-canary: adapter SHA-256
  `5686ee98e8ed09cd31f3f0228dd4cfec60fd58907090b5ec71372c83571f7da4`;
  empty count 0; summary SHA-256
  `aa35cb7bea41248ede7061d2c244861d22338461eb152f63c06822726ee5a9b9`.
- corrected-r2 control: adapter SHA-256
  `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`;
  empty count 0; summary SHA-256
  `ec4ad316e99aec9a3339338fa38800434a731d61abb5afb15a368f95a5efbf9e`.

Result summaries are committed under
`training/journal/phase108-public-functional-44589/`; they contain probe IDs
and response metadata only, not prompt or generated text. The job and client
SHA-256 values were respectively
`a3ec1ec17d63149c324b36d6ebb29a6cab9e8067a03de14bdf9013eef9e888c1` and
`ccb520086ed240b8321ef4e948f62f48052f4cb5fc55337a0233f9bdc40c88c6`; the
server SHA-256 was
`df1484bd0b01ee72e3b41dbb2a7ceda7b384d1e08f99239ffde68357338f83f7`.
Post-run weight hashes matched the pinned values, and process inspection found
no lingering candidate API process.

This says only that these candidates can serve non-empty output for four
specific development probes under this GPU/runtime and sampling setup. It
does not assess answer correctness, professional capability, stability under
other prompts, or eligibility for blind evaluation/promotion. The separate
scale-20 immediate-EOS issue on the previously exposed 16-prompt diagnostic
remains unresolved. No persistent endpoint, SSH tunnel, production setting,
adapter weight, rubric, protocol, permission, or blind-suite content changed.
