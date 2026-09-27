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

## Results

Pending successful retry. If successful, record only per-scale validation
loss, row count, immutable hashes, runtime, and split-read flags here. Do not
interpret lower loss at a non-training scale as a quality or safety gain.
