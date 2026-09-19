# 2026-09-19 — Phase 106 result and Phase 107 evaluation audit

## Work performed

- Completed the 360-case GLM-5.2 retry at `max_tokens=3000`; one transient error for p104-291 was retried successfully.
- Finalized canonical response-only results without provider `reasoning_content` and computed the unchanged Phase 104 mechanical rubric: 311/360. Counts: 279 `stop`, 81 `length`, 18 empty final answers.
- Re-checked the original comparison log: DeepSeek 358/360 at 900 tokens; GLM 180/360 at 900 tokens; Phase 91 346/360 at 900 tokens; Phase 105 344/360 at 900 tokens. The 3000-token GLM run is not a matched comparison. Phase 105 remains below production.
- Audited the Phase 104 manifest: 360 IDs/exact prompts, but only 45 prompt cores after removing the known category wrappers and numeric case labels. The largest core group has 40 rows. This fails the requested 300-independent-case gate and invalidates the earlier “360 independent cases” characterization.
- Expanded exact-overlap scanning to include all 149 user dataset batches, split-named Phase files, and `user`-field samples. Across 188 local JSONL files / 22,315 rows, the Phase 104 manifest had zero exact prompt overlaps; no parse/unrecognized rows. This is not semantic or pretraining contamination proof.
- Ran dataset CI validator: 21,799 records across 149 files; passed configured checks.
- Wrote a Phase 107 benchmark design draft and reproducible diversity/overlap scripts. No replacement benchmark prompts have been accepted yet.

## Negative findings and limitations

- Phase 104 reused the same 40 security prompts across four strata with wrapper prefixes; five behavior/format strata each repeated one scenario 40 times. IDs and hashes obscured the scenario duplication.
- GLM's 3000-token result cannot be ranked directly against 900-token runs. Rubric is heuristic and has no independent semantic review.
- Exact overlap scan cannot find paraphrases, unsupported formats, data sources outside the local tree, or foundation-model pretraining exposure.
- This repository does not contain the Phase 104 raw case manifest or raw model outputs. Only aggregates, hashes, and scripts are tracked; private prompts/outputs and raw reasoning are kept out of Git.

## Production and training status

- No model training started.
- No adapter/base model, API, Harness, or tool permission changed.
- Phase 91 remains the production checkpoint; Phase 105 remains isolated.
- Next gate: write and audit at least 320 truly distinct private defensive scenarios (40 × 8 required strata), then freeze a new rubric and matched inference protocol before running Phase 91 plus two references. Do not use Phase 104 scores for parity claims.
