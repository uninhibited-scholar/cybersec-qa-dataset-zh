# Phase 107 private suite — draft audit

Date: 2026-09-19

Status: private candidate set generated; rubric not frozen; no model scoring performed.

## Generation and integrity

- Cases: 320 total, 40 in each of eight strata.
- Unique fixture IDs: 320; unique exact prompts: 320; unique normalized prompts: 320.
- Targeted scenario-core normalization: 320 distinct cores; largest repeated core group: 1.
- Answer keys: 320, stored separately from prompts and excluded from model inputs.
- Source fixture SHA-256: `6c0e65be55826cd04f5f0e7be1ebd5fd290b0f3062ffff4cbd58e48eb1d45656`
- Generated manifest SHA-256: `5f76a665febcb46f63c25c19556c1127cb603238cc046b7f8154fc8a9531d40d`
- Generated answer-key SHA-256: `37657febdddc089d0ff7153cb0c62bd06162ee3eff69feca8ffba9d20614ece5`

## Exact-overlap scan

- Scope: 188 local JSONL files (train/validation/test and numbered source batches); 21,946 normalized prompt/key strings indexed.
- Parse errors: 0; unrecognized rows: 0; exact normalized overlaps: 0.
- Result: `no_exact_overlap_in_scanned_scope_not_clean_certification`.
- Limitations: no semantic near-duplicate detection, no guarantee that every checkpoint used only these scanned files, and no claim about foundation-model pretraining exposure or external sources.

## Strata

| Stratum | Cases |
|---|---:|
| Vulnerability analysis | 40 |
| Detection and remediation | 40 |
| Threat modeling | 40 |
| Code review | 40 |
| Evidence boundaries | 40 |
| Multi-turn reasoning | 40 |
| Tool honesty | 40 |
| Prompt injection | 40 |

## Gates still open

1. Independent semantic review of scenario independence, answer keys, ambiguity, and rubric alignment.
2. Freeze a new rubric and matched inference protocol before any model scoring; Phase 104 rules stay unchanged.
3. Only then run Phase 91 and at least two references under identical prompts, tools, context, decoding, token budget, retries, and parser. Keep the candidate bank and answer keys local and separate.

No training, production API/Harness change, permission expansion, or model run occurred during this work.
