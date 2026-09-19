# 2026-09-19 — Phase 107 multi-turn schema correction

## Finding

Inspection of the ignored Phase 107 manifest showed all 320 items had only a `prompt` string. The 40 `multiturn` entries referred to “round 1/2” inside short prose, but contained no structured message sequence; this would have tested single-turn transcript interpretation rather than multi-turn context handling.

## Correction

- Updated the deterministic local-only builder to emit an authoritative `messages` array for every case. Single-turn items have one user message. Multi-turn cases have a shared, fixed user/assistant/user interaction sequence: initial evidence and provisional request, a neutral acknowledgment that maintains uncertainty, and the follow-up evidence/task.
- Retained each original prompt as an audit-only source field; the inference protocol now requires runners to send `messages` only and never concatenate both fields.
- Added builder and diversity checks plus unit tests for the three-message role order and extraction of follow-up requests.
- Added `phase107_suite_validate.py`, a privacy-preserving structural validator that checks stratum counts, case/key correspondence, hashes, role order, unique multi-turn histories, and answer-key schema without printing prompts. Unit tests cover full synthetic-suite acceptance and answer-key mismatch rejection.
- Generated a new ignored local v0.2 manifest and answer-key artifact, preserving the prior v0.1 files. Manifest SHA-256: `6d75567be1ec32e1599951e98776625e93b4cc1826a269ff8b4f59304306d982`; answer-key SHA-256 remains `37657febdddc089d0ff7153cb0c62bd06162ee3eff69feca8ffba9d20614ece5`.

## Verification and boundaries

- 320 cases, 40 per stratum; 320 unique IDs/prompts/normalized cores; all 40 multi-turn cases are structured user/assistant/user sequences, with 40 distinct user-message histories; no invalid sequence.
- Correct parent-root overlap scan: 188 JSONL files / 22,315 rows, 21,946 indexed strings, no parse errors, no unrecognized rows, and no exact overlap with the v0.2 prompts/answer keys.
- Manually inspected only the four low-threshold lexical near-duplicate pairs flagged by the scanner. They share some terminology but assess distinct evidence/decision points; this is a limited pair review, not an independent semantic audit of all 320 cases.
- `phase107_suite_validate.py`: pass, 320 cases/keys, 40 valid distinct multi-turn histories, 0 structural errors.
- `python -m pytest -q`: 8 passed.
- Private case/key artifacts remain gitignored. No prompt was sent to any model; no scores, training changes, production changes, or criterion changes were made. The evaluation rubric and protocol remain drafts pending explicit approval.
