# 2026-09-19 — Phase 107 static integrity recheck

## Work performed

- Re-ran the targeted scenario-diversity audit over the ignored local Phase 107 manifest: 320 rows, IDs, exact prompts, and normalized cores; 40 rows in each of the eight strata; largest duplicate-core group 1.
- Re-ran the exact normalized overlap audit with the separate answer keys and correct scan root (`..`, the parent `ni-a/` directory). It covered 188 local JSONL files / 22,315 rows and 21,946 indexed prompt strings; 0 parse errors, 0 unrecognized rows, and 0 exact overlaps. The 320 case IDs exactly match 320 answer-key IDs.
- Resolved a root-scope discrepancy: running the scanner from `.` only sees the 149 dataset batch files; it omits 39 sibling Phase train/valid/test files. That incomplete invocation was discarded. The parent-root invocation reproduces the previously recorded 188-file scope.
- Ran repository tests: `python -m pytest -q` → 3 passed.
- Confirmed prompt manifest and answer keys remain gitignored. No raw case, key, or model output was displayed, edited, sent to a model, or added to Git.

## Boundaries and outcome

- This was static integrity validation only; no Phase 107 prompt was sent, no score was generated, no training was run, and Phase 91 production was not changed.
- Exact overlap does not establish semantic independence, checkpoint lineage, or absence from foundation-model pretraining. The manual scenario-family/answer-key review and frozen rubric/protocol gates remain open.
- Phase 107 private rubric and inference protocol remain drafts pending explicit user approval. Both reference runtime smokes are readiness checks, not quality measurements.
