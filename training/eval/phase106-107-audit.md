# Phase 106/107 evaluation audit — 2026-09-19

## Decision

Phase 104/106 is retained as historical diagnostic evidence only. It does not meet the 300-independent-case requirement and cannot support a claim of parity with leading models. Phase 105 remains below Phase 91 and is not deployable. No training, production API, adapter, tool permission, or scoring threshold was changed in this audit.

## Phase 104 scenario diversity

- Manifest: 360 rows, 360 IDs, 9 nominal strata × 40.
- Exact prompts: 360. After stripping known category boilerplate and case-number prefixes: **45 underlying prompt cores**; largest repeated core group: 40.
- Root cause: the same 40 security topics were reused across four strata with only a task prefix changed; five behavior/format strata each repeated one base scenario 40 times with different numbers.
- Manifest SHA-256: `56eaa0f7fdff51af73b02d8ece1e48e1872901339287690a4d93325a84171124`.
- Reproducible count audit: `training/scripts/phase107_manifest_diversity.py`; output: `training/eval/phase104-diversity-audit.json`.

## Exact overlap scan

- Scope: 188 local JSONL train/valid/test split files and dataset batch files, including all 149 `cybersec-qa-dataset-zh/batchNNN.jsonl` files.
- Parsed rows: 22,315; indexed unique user prompts: 21,934; parse errors: 0; unrecognized rows: 0; exact prompt overlaps with Phase 104: 0.
- This excludes semantic paraphrase detection, unsupported file formats, remote corpora, checkpoint lineage, and foundation-model pretraining exposure. Therefore this is an exact-overlap result, **not** a clean-contamination certification.
- Reproducible scanner: `training/scripts/phase107_overlap_audit.py`; output: `training/eval/phase104-overlap-audit.json`.
- Dataset CI validator: 21,799 records / 149 batches, passed its schema, duplicate, minimum-length, and configured purity checks.

## Reference results and protocol caveat

| Run | Mechanical score | Completion cap | Notes |
|---|---:|---:|---|
| DeepSeek v4 Flash | 358/360 | 900 | Diagnostic; weak Phase 104 scenario diversity |
| GLM 5.2 original | 180/360 | 900 | 158 empty final bodies in 360 successful unique cases; 328 initial transport-error attempts were retried |
| GLM 5.2 higher-budget retry | 311/360 | 3000 | Diagnostic only; not directly comparable to the 900-token runs |
| Phase 91 production | 346/360 | 900 | Existing local result; no runtime mutation |
| Phase 105 candidate | 344/360 | 900 | Below Phase 91; remain isolated |

The GLM higher-budget retry canonicalized 360 successful IDs from 361 attempt rows (one transient error followed by a successful retry). It recorded 279 `stop`, 81 `length`, and 18 empty final answers; the 18 empty answers were all `length`-terminated. Under the unchanged Phase 104 mechanical rubric its strata were 36/40 cyber accuracy, 34/40 detection/remediation, 28/40 threat modeling, 31/40 code review, 40/40 each for evidence boundary, multi-turn, tool honesty, and prompt injection, and 22/40 format/general. The rubric is heuristic, not semantic adjudication.

The 3000-token GLM run has a different generation budget from the other rows. Do not compare its aggregate rate directly to DeepSeek or Phase 91 as a controlled head-to-head result. Original and retry artifacts remain outside Git because they contain prompt/output data; the raw retry also contains provider-returned reasoning content. Only hashes and aggregate counts are committed.

## Next gate

Create a genuinely diverse private benchmark with at least 40 distinct underlying cases in each of the eight required strata (320 total). Keep answer keys separate, run exact and normalized overlap checks against every available train/valid/test source, manually audit scenario families, and freeze any new rubric as a separate version before model scoring. Rerun Phase 91 and at least two reference models on the identical manifest, system prompt, context, tools, token budget, retry policy, and parser. Do not train a candidate or deploy based on Phase 104/106 scores.

The Phase 107 design draft cites public methodology from [Meta CyberSecEval 4](https://github.com/meta-llama/PurpleLlama/tree/main/CybersecurityBenchmarks), [SEC-bench](https://github.com/SEC-bench/SEC-bench), and [NIST SSDF SP 800-218](https://csrc.nist.gov/pubs/sp/800/218/final); public tasks will remain separate from the low-contamination private set.
