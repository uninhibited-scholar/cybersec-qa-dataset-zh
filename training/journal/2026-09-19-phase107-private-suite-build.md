# 2026-09-19 — Phase 107 private suite build

## Work performed

- Authored a local-only 320-case defensive cybersecurity evaluation draft across eight strata (40 each): vulnerability analysis, detection/remediation, threat modeling, code review, evidence boundaries, multiturn reasoning, tool honesty, and prompt injection.
- Kept private source fixtures, generated prompt manifest, answer keys, and detailed overlap output gitignored. Added a deterministic builder under `training/scripts/` and made `--require-full` enforce the 320 / 40-per-stratum gate.
- Builder validation passed: 320 rows, 320 IDs, 320 normalized prompts, 320 answer keys. Scenario-core audit found no repeated core after the targeted wrapper/number normalization.
- Exact normalized overlap scan against the local tree, including answer-key phrases: 188 JSONL files, 21,946 indexed normalized prompt/key strings, 0 parse errors, 0 unrecognized rows, 0 exact overlaps.
- Drafted a separate Phase 107 rubric (0–8 per case plus non-averaged critical-failure labels), paired reporting, and blind-review protocol. It is explicitly not frozen; no scores were produced.
- Revalidated the live baseline over SSH: the Mac mini API health is `ok`; launchd confirms the production base `Qwen3-4B-mlx-4bit-phase3-wrapper` plus adapter `phase99-multiturn-candidate` on port 18765. No completion request was sent.
- Confirmed the Slurm account is reachable, A100-40G partitions are listed, and no job is queued/running. Mini reference files include Gemma 3 4B MLX plus larger Gemma 4 26B and GPT-OSS 20B GGUF files; large references should use an isolated A100-compatible runtime, not load alongside the 16 GB production mini.
- Recorded only aggregate counts and hashes in the tracked audit report; no prompt text, answer keys, model responses, or credentials are committed.

## Limitations and next gates

- This is a draft benchmark, not a frozen or independently adjudicated rubric. No model was scored.
- Exact matching does not detect paraphrases, off-tree sources, checkpoint lineage gaps, or foundation-model pretraining exposure. The scenario-core script is targeted normalization, not a general semantic-similarity proof.
- Before comparison, reviewers must adjudicate ambiguity and answer-key/rubric consistency; freeze a distinct Phase 107 rubric and matched inference protocol. Do not alter Phase 104 scoring.

## Production and training status

- No training started; no candidate weights changed.
- Phase 91 production, API, Harness, tool permissions, and active adapter were not touched.
