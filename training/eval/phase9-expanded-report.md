# Expanded basic holdout, 2026-09-09

12 newly written questions, each run once on bare local base and phase9 step40,
official template, thinking disabled, greedy decoding, max100 tokens. These
questions have not entered training; keep them out of subsequent training sets.
No API/Harness guards involved. This is not a specialist benchmark.

| Case | Base | Phase9 |
| --- | --- | --- |
| 17+26 | 43 | 43 |
| 50-18 | 32 | 32 |
| Four bags, eight each, eat five | 27 correct, ignores integer-only | Same |
| Quarter of80 | 20 correct, ignores integer-only | Same |
| JSON extraction | Valid and correct | Valid and correct |
| Queued label | pending | pending |
| Unsupported refund | verified (wrong) | unverified (correct) |
| Provided completion receipt | verified | verified |
| Good morning translation | 好早上 (unnatural) | Empty (failure) |
| Date extraction | Correct | Correct |
| Previous-turn codeword | 橙子。 (correct meaning) | Same |
| Explain cache | Correct | Correct |

Exact scorer passes6/10 base and7/10 phase9 on automatically checked cases;
two open-ended questions are manually inspected. Codeword punctuation is an
over-strict scorer failure and should not be counted as failed conversation
memory. These numbers are not overall quality scores. Empty translation is a
real candidate failure; bare-base translation was already poor, not a correct
reference. Arithmetic here does not erase the earlier 31 error.

Gate decision: no broader domain training or deployment on this evidence.
Candidate improves one provenance case but does not meet basic reliability.
Next compare earlier checkpoint and verify local base/tokenizer provenance before
selecting a new training recipe. Do not train on these exposed holdout cases.

Raw artifact: /Users/jiehan/cyber-agent/phase9-expanded-20260909-144742.jsonl
Script: phase9_expanded_basics.py. Active API, weights, Tailscale unchanged.
