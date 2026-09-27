# Phase108 v1.8-rev2 blinded collection — Slurm 44803

## Completion and integrity

- Slurm job `44803` on `titanv1`: `COMPLETED`, exit `0:0`, elapsed `03:46:09`.
- Collection log: `logs/phase108-v18r2-blind-44803.log`; stderr reports all four unit tests passed (`Ran 4 tests ... OK`). The collection log records `unit_tests_complete` before inference.
- Preflight reported hash verification for all seven pinned inputs/scripts: frozen private-case set, freeze manifest, numbered and final adapters, collector, adapter smoke test, and collector tests.
- Private result directory mode `0700`; manifest, runtime metadata, aggregate, identity map, and each response file mode `0600`.
- Three arms each contain 320 JSONL records (960 total). No content rows were opened for this audit.
- `aggregate.json` SHA-256: `96f663e515501141be460b87e9b5e0a5bbeacc0d5146a7c61083a8fbcdde8156`; matches the completion log.
- Response-file hashes match the per-arm completion records in the job log:
  - A: `9a2dc72766c915501999174db225fc9ceb14d618840829de4e62fe88f55670a5`
  - B: `516582dab87dde4dd6fcb74e0acef9e566982987dba655d1194ca7cc24f8ee27`
  - C: `47be89fbef8a6ef0bff6cbb766c96066e381ee0706e04b66a1ae9fe7061f902f`
- Completion metadata says `blind=true`, `scores=false`, `promotion_eligible=false`, `production_changed=false`; no alias map or answer key was opened during collection or this integrity check.

## Blinded aggregate diagnostics only

These are structural generation diagnostics, not quality scores. Arm identities remain blinded.

| Arm | Cases | Empty | Finish reasons | Tool marker | Median latency (s) |
|---|---:|---:|---|---:|---:|
| A | 320 | 297 | stop 319, length 1 | 0 | 0.0981 |
| B | 320 | 3 | stop 97, length 179, other_stop 44 | 19 | 40.6157 |
| C | 320 | 298 | stop 319, length 1 | 0 | 0.0983 |

Collection elapsed time in the log: `13468.474` seconds. The large empty-output split and B's unusual latency/finish profile are material anomalies. Do not unblind, score, select a candidate, or promote based only on these diagnostics. Preserve the blind key; next work should be an independent, blinded semantic/format/honesty review and the fixed regression gates using the sealed protocol.

## Scope

Only sanitized aggregate metadata is recorded here. Raw prompts/responses, alias map, answer key, and model weights remain on the cluster and are not committed. Production API/adapters, rubric/protocol, permissions, validation data, and candidate weights were not changed.

## Integrity-verifier follow-up

The first post-collection integrity job (`44837`) was terminal `FAILED` with
Slurm reason `Dependency`; it produced no report. A resubmission (`44907`) also
exited before running its verifier. Its silent shell precondition failure was
traced to the wrapper looking for Python under the project directory, while
the installed environment is `$HOME/miniforge3/envs/coevo`. After correcting
that path, verifier job `44909` ran its four unit tests but rejected the
collection because compute nodes cannot connect to SlurmDBD (`localhost:6819`
connection refused), so `sacct` cannot be queried from the compute allocation.
The authoritative login-node `sacct` query succeeds and reports `44803` as
`COMPLETED`, `0:0`.

Corrected both tracked CPU wrappers to resolve that established environment
path. The verifier now accepts a fresh, explicit login-node `sacct` snapshot,
records its source and observation time, and still rejects any state other
than `COMPLETED`/`0:0`; its normal direct-`sacct` path remains available. The
output is written to a job-specific temporary file and renamed only on
success. The blind-review wrapper requires an explicit `INTEGRITY_JOB_ID`
rather than carrying a stale hard-coded dependency. Shell syntax passed; local
synthetic tests passed 6/6 for the integrity verifier and 5/5 for the review
packer. Failed job `44909` left a zero-byte mode-0600 report placeholder; it
was preserved as `integrity-report.failed-44909.empty` and is not treated as a
successful report. Verifier job `44915` then completed `0:0`; all six
synthetic tests passed and the output reports
`verified_blind_collection_integrity`, 320 rows per arm, the pinned
parent/candidate/freeze/cases hashes, `identity_map_read=false`,
`labels_revealed=false`, and `deployment_approval=false`. The private report is
mode `0600`, 1,647 bytes, SHA-256
`523ded4587c7c6301f1b6ddd5c92d7dc1cf896fdec113c59ad1412a092ddcd54`. Its
login-node `sacct` snapshot for 44803 was observed at
`2026-09-27T15:44:03+0800` and recorded `COMPLETED`/`0:0`.

The answer key and identity map remain unopened. The packer was adjusted to
consume the integrity report's verified collection snapshot plus an explicit,
fresh login-node `sacct` snapshot for the verifier job; it still reruns all
collection hash/schema checks and never reads the identity map.

The first packer submission (`44916`) exited during a path precondition,
before unit tests or bundle generation: its answer-key path incorrectly pointed
under `data/`. The key was located by filename only at
`results/phase108-train-leak-scan-v18r2/`; its parent is mode `0700`, the file
is mode `0600`, and its SHA-256 matches the frozen pin
`f79828a550fb80cd84aba7faa593cd84a4f47e08ee8afc358957726de17a4015`.
No key content or identity map was opened by the failed attempt. The tracked
packer wrapper now points to this sealed artifact; rerun only after syncing
and hash-checking that wrapper.
