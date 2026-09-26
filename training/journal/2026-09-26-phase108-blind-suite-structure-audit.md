# Phase108 blind-suite structure audit — 2026-09-26

## Scope

Read-only structural audit of the two current private fixture source banks.
No prompt text, answer key, rubric, protocol, or source fixture was changed or
copied into Git. These counts are not semantic-independence proof and do not
authorize freezing the blind suite.

## Pinned sources

- Bank A SHA-256:
  `eb36aceb11eb473160083bb67139f5d34b0a3995335d699d492c52efb047fb5c`.
- Bank B SHA-256:
  `8f085994be4f2315b92ef930fd9c7a75a8c396f60845752bdd9aaeb49e4121f5`.
- Each category currently has 40 cases and 40 distinct scenario-root IDs.

## Output-format coverage observed

The current `format_contract` / prompt distribution is structurally narrow:

| Category | Unique format contracts / 40 | Largest repeated contract | Explicit JSON requests |
|---|---:|---:|---:|
| code review | 1 | 40 | 0 |
| detection/remediation | 1 | 40 | 0 |
| evidence boundary | 40 | 1 | 0 |
| multi-turn | 1 | 40 | 0 |
| prompt injection | 1 | 40 | 0 |
| threat modeling | 1 | 40 | 0 |
| tool honesty | 9 | 32 | 0 |
| vulnerability analysis | 1 | 40 | 0 |

The simple explicit-format scan also found only 0–3 bullet-format prompts per
category and no more than 2 table-format prompts in a category. These are
aggregate structural counts, not judgments about the underlying scenario
quality. `format_contract` diversity alone is not enough: the request must be
explicit in the prompt and the scoring key must match that request.

## Decision and next work

Do not freeze or use the current 320-case composition as sufficient format
regression evidence yet. Create a separately versioned private revision with
balanced, explicit output contracts across relevant categories; keep scenario
facts independent; align each private key to the exact requested format; then
rerun contamination, duplicate/near-duplicate, and independent semantic
review against the new hashes. Keep the current banks immutable for lineage.
The scoring rubric and inference protocol remain unchanged.
