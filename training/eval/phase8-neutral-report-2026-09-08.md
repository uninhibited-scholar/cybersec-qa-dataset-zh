# Phase 8 pilot: no demonstrated improvement

## Protocol

Eight fixed ordinary-language questions, phase5-best120 versus phase8 step40.
Raw MLX weights, tokenizer ChatML, no system prompt, no API guard, greedy
decoding, max_tokens=180, enable_thinking=False. One run per question. This is
a diagnostic comparison, not an external or blinded benchmark. Questions were
written after training, but this small suite cannot estimate overall ability.

## Observations

| Case | Phase 5 | Phase 8 |
| --- | --- | --- |
| Unsupported cancellation claim | Empty answer | Empty answer |
| Accepted job | Correctly distinguishes acceptance/completion; cut off | Same distinction; cut off |
| Failed conversion | Recognizes failure; cut off | Same; cut off |
| Completed receipt | Correct core facts; leaks `回答：` | Outputs unrequested `回答不超过100字`; calls job ID a returned result |
| Unsupported upload history | Empty answer | Empty answer |
| Arithmetic | 29 correct, repeated until limit | Same repeated answer |
| Two bullet points | Duplicates input before numbered points | Same |
| Translation | Correct translation plus unrequested instruction text | Same |

The 180-token cap explains incomplete long answers; do not count all truncation
as model failure. Empty answers, unsolicited instruction text, and repeated
arithmetic are independently observable problems under these decoding settings.
No bare-base comparison was run, so these findings do not isolate adapter damage
from wrapper/template/decoding behavior.

## Live Harness, current Phase 5 route

A new browser conversation submitted a combined arithmetic/status/translation
prompt with tools explicitly disabled. Visible response completed in 56 seconds
(UI time, not a speed comparison while other inference was active).

- Arithmetic first said 15, later 29: contradictory response.
- Accepted status was not treated as proof of completion, but the explanation
  overstated what null results imply about execution/failure.
- Translation was correct.
- Generated conversation title was unrelated to the actual questions.

This is a current-route integration observation, NOT a Phase 8 Harness test.
No serving adapter was switched.

## Decision

Keep pilot weights as a negative experiment. Do not deploy or expand the same
training recipe based only on decreasing validation loss. Next diagnostic:
compare unadapted base and both adapters with identical actual worker prompts,
inspect early EOS, and separate prompt/template and repetition effects before
another training run. New broad holdout is still outstanding.

Raw output: /Users/jiehan/cyber-agent/phase8-neutral-compare-20260908.jsonl
Reproduction: training/eval/phase8_neutral_compare.py (refuses output overwrite).
