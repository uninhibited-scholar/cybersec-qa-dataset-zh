# Phase 107 private suite — draft audit

Date: 2026-09-19

Status: private candidate set v0.2 generated; rubric/protocol not frozen; no model scoring performed.

## Generation and integrity

- Cases: 320 total, 40 in each of eight strata.
- Unique fixture IDs: 320; unique exact prompts: 320; unique normalized prompts: 320.
- Targeted scenario-core normalization: 320 distinct cores; largest repeated core group: 1.
- Character 3/4/5-gram TF-IDF triage at the deliberately low 0.10 threshold flagged four pairs (maximum similarity 0.1237); each pair was manually inspected in the local private manifest. The flagged pairs are distinct decision contexts (including config metadata vs alert-rule metadata, SAML binding vs URL-fetch review, CSRF vs OAuth cookie behavior, and translation vs report summarization), not duplicate cases. This lexical check still cannot prove general semantic independence.
- Answer keys: 320, stored separately from prompts and excluded from model inputs.
- Source fixture SHA-256: `6c0e65be55826cd04f5f0e7be1ebd5fd290b0f3062ffff4cbd58e48eb1d45656`
- Generated v0.1 single-string manifest SHA-256 (superseded for execution): `5f76a665febcb46f63c25c19556c1127cb603238cc046b7f8154fc8a9531d40d`
- Generated v0.2 manifest SHA-256: `6d75567be1ec32e1599951e98776625e93b4cc1826a269ff8b4f59304306d982`
- Generated answer-key SHA-256: `37657febdddc089d0ff7153cb0c62bd06162ee3eff69feca8ffba9d20614ece5`
- v0.2 uses an explicit `messages` sequence as the authoritative request field. All 320 single-turn items become one user message; the 40 multi-turn items are distinct ordered user/assistant/user conversations (40 unique user-message sequences). The original `prompt` is retained only as an audit/source field. The prior v0.1 generated artifact remains local and is not the execution manifest.

## Exact-overlap scan

- Scope: 188 local JSONL files (train/validation/test and numbered source batches); 21,946 normalized prompt/key strings indexed.
- Parse errors: 0; unrecognized rows: 0; exact normalized overlaps: 0.
- Result: `no_exact_overlap_in_scanned_scope_not_clean_certification`.
- Limitations: no semantic near-duplicate detection, no guarantee that every checkpoint used only these scanned files, and no claim about foundation-model pretraining exposure or external sources.

## Runtime and reference availability re-check

- Mac mini SSH is reachable; `com.uninhibited-scholar.cyber-agent-api` is running on the mini and its local `/health` returned `{"status":"ok","model":"qwen-cyber-local"}`.
- launchd reports the active model path `Qwen3-4B-mlx-4bit-phase3-wrapper` and adapter path `phase99-multiturn-candidate`; the API listener is on port 18765. No completion requests were sent.
- The school Slurm account is reachable and has A100-40G partitions listed; `squeue` showed no running or queued job. The cluster migration copy contains a dequantized base, so it is not substituted for the live MLX production endpoint.
- The mini has local reference candidates including Gemma 3 4B MLX (about 2.1 GB), Gemma 4 26B GGUF (about 16 GB), and GPT-OSS 20B GGUF (about 11 GB). The two larger references should not be loaded alongside the mini's live production service; the Slurm A100 route needs an isolated, format-compatible runtime check before use. No model was loaded for this check.

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
