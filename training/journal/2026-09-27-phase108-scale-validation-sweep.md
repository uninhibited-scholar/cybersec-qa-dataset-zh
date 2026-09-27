# Phase108 scale-validation sweep — 2026-09-27

## Purpose and fixed boundary

Measure the corrected-r2 candidate's loss on the frozen validation split at
MLX direct scales 1, 2.5, 5, 10, and 20. This is a scale-sensitivity
diagnostic only, not a capability score, inference-scale selection, blind
result, or deployment gate. The job is designed to read only the pinned
`valid.jsonl`; train/test splits, blind suites, APIs, production weights,
tools, and permissions are out of scope.

Pinned inputs are candidate adapter SHA-256
`4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`,
candidate manifest SHA-256
`e60ae88a3f491ed94b13f9e26ef0892e5986c838f69dff2fcbf8714185a29636`, and
validation SHA-256
`44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365` (1,089
rows). The runner, scale provenance checker, scale utility, and both focused
test files are hash-pinned in the Slurm wrapper. The two multi-GB base shards
are verified by SHA-256 inside the scheduled allocation, never on the login
node. Output is one metadata JSONL in a unique job path with mode 0600; no
prompt/completion contents are emitted.

## Attempt 45022 — infrastructure failure before inference

Slurm reports `45022` failed with exit code `1:0` after 18 seconds on
`titanv1`. The four adapter-loader tests passed, then importing the LoRA-scale
test module failed because its test-only import uses the repository namespace
`training.scripts`, which was not on `PYTHONPATH`. No model was loaded; no
scale validation or generation occurred; the result JSONL was not created.
This is an execution-environment failure, not model evidence.

The wrapper was corrected to set `PYTHONPATH` to the synced project data root
before invoking the tests. The retry must use a fresh Slurm job/output path,
rehash the changed wrapper, and repeat all pinned input checks before running
any model inference. No production or candidate artifact changed.

## Attempt 45029 — provenance guard stopped a mistyped parent hash

Slurm reports `45029` failed with exit code `1:0` after 13 seconds on
`titanv1`. All seven focused unit tests passed, including the corrected
namespace import. The no-inference provenance checker then rejected the
wrapper's expected parent-adapter digest before loading the model. The pinned
candidate manifest SHA-256 is still
`e60ae88a3f491ed94b13f9e26ef0892e5986c838f69dff2fcbf8714185a29636`, and its
recorded input adapter SHA is
`3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`; this
matches the prior fixed-validation and parent-adapter records. A similar but
mistyped digest (`...149833...`) in the new wrapper caused the rejection.
The guard worked as intended: no model inference occurred and no output file
was created. Fix only the expected digest, retain this failed attempt, and
retry under another fresh job ID after syncing and checking the wrapper hash.

## Retry 45030 — completed successfully

After correcting the Python namespace and exact parent-source SHA, the wrapper
passed remote syntax and provenance preflight. The no-inference checker
reported the pinned candidate SHA, rank 8, MLX scale 20, PEFT alpha 160,
effective scale 20, and `test_split_read=false`. Seven adapter/scale unit tests
passed inside the scheduled job before model loading. Job `45030` completed
successfully on `titanv1` with exit code `0:0` after 1:23:53; wrapper SHA-256 is
`5102e49130e9c6668aa7badf87be2597f0a37c9ea8deb9fac8d0569eb888ee0e`.

The final aggregate contains exactly five rows, all `status=complete`, all
with 1,089 validation rows, frozen validation SHA
`44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365`, candidate
adapter SHA `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`,
and `train_split_read=false`, `test_split_read=false`,
`production_approval=false`:

| Diagnostic scale | Validation loss | Rows | Frozen validation SHA | Train/test read |
| ---: | ---: | ---: | --- | --- |
| 1.0 | 2.0980716427 | 1,089 | `44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365` | neither |
| 2.5 | 2.0298910662 | 1,089 | `44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365` | neither |
| 5.0 | 1.9416260420 | 1,089 | `44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365` | neither |
| 10.0 | 1.8159374347 | 1,089 | `44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365` | neither |
| 20.0 | 1.7063122642 | 1,089 | `44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365` | neither |

All five rows record the same immutable adapter SHA-256
`4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`, rank 8,
and the expected PEFT alpha/effective scales (8/1, 20/2.5, 40/5, 80/10, and
160/20). The aggregate JSONL SHA-256 is
`b47d979d473435f1320a7b8d6173232bf46b48f5019aba95d6fa34ee5202adeb`; the
copy in `training/eval/phase108-r2-valid-scale-sweep-45030.jsonl` matches the
remote file hash. The terminal log contains
`PHASE108_SCALE_VALIDATION_SWEEP=PASS scales=1,2.5,5,10,20 rows_per_scale=1089`
and the expected output hash. The retry wrapper hash matches the pinned value.

These are validation-loss sensitivity measurements only, not a capability or
safety comparison and not an inference-scale or deployment selection. Lower
loss at larger scales does not establish better behavior. The stage is now
complete and is paused at the user's request; no further training, blind
evaluation, production change, or promotion was initiated.
