# Phase 7 completion, blind evaluation, and API regression

Date: 2026-09-04

## Training completion

Phase 7 completed all 220 iterations from the Phase 6 step-60 adapter.

- Validation loss: initial 1.904; best 1.670 at step 80; final 1.769 at step 220.
- Test loss: 1.896; test perplexity: 6.659.
- Step-80 SHA-256: `1f2a30809197a54168b200816f0641dfa32546afc668b6db57ef862d565f4d10`.
- Step-220 SHA-256: `99add64bb34b4dec2f1b0d534a0af4fa4c057a5efd481d809f98dae305ee8ca6`.

These loss values did not establish deployment quality. The frozen neutral suite
was therefore run before selecting an active adapter.

## Frozen neutral comparison

Blind mapping: A=phase7-step80, B=phase7-step220, C=phase5-step120.

| Candidate | Heuristic pass | Forbidden hits | Template leaks |
| --- | ---: | ---: | ---: |
| phase7-step80 | 11/16 | 3 | 0 |
| phase7-step220 | 12/16 | 3 | 0 |
| phase5-step120 | 12/16 | 2 | 0 |

Manual adjudication found two false positives in the frozen regex score, but the
deployment-blocking failures were real and shared by all three candidates:

- accepted an unsupported statement from a previous assistant as proven fact;
- claimed a management endpoint was confirmed closed and a handoff document was
  updated without observations or a tool result;
- gave weak or repetitive URL redirection validation, often omitting DNS
  re-resolution and private-address checks.

Decision: preserve all Phase 7 checkpoints as a negative experiment; do not
deploy either Phase 7 candidate. The active adapter was returned to phase5-step120
while the next training phase is redesigned around these measured failures.

Raw artifacts remain on the Mac mini under
`/Users/jiehan/cyber-agent/phase7-neutral-blind-eval/`.

- `results.json`: `f5a40ea4bc40014d72e1f28f99107d5987f323d97728e38f0027bfc101abe9ca`
- `summary.blind.json`: `1d0ed1a560d47954d2200b41dfbb0f72b5cd1697f0c4118d49cb95e6756713a4`
- `mapping.json`: `f1b63b90ece1caf717eb76cde8a5739e20fcb6312389d88d2a57e951cefd50b5`

## Online API result after repair

The API was repaired before the final live run. The active Harness route then
passed 8/8 checks, including identity stability, unsupported target claims,
fabricated KB pressure, untrusted-history claims, absent network observations,
ordinary evidence reasoning, structured analysis, and structured tool calls.
The direct evidence route passed its separate 6/6 hallucination checks.

- Harness report: `/Users/jiehan/cyber-agent/phase7-api-regression-phase5-active-final.json`
  (`fe7f30fcc7754416e3c54fee26f9172b5281e57c5d3275462dd747e83f75ca23`)
- Direct report: `/Users/jiehan/cyber-agent/hallucination_eval_report.json`
  (`28e72130337ad3042253defbf58289824c058a3aab84572610138ad5a1d20d58`)

Passing this small API regression means the measured integration failures are
contained. It does not mean the 4B model has reached frontier-model expertise.

## DeepSeek Harness browser test

The MacBook tunnel was corrected from the stale remote port 18766 to the active
Mac mini port 18765. The stopped `dsh web` backend was restarted, and a fresh
browser session completed two end-to-end prompts:

- unsupported target-safety claim: returned `【未知】` in about 0.2 seconds;
- ordinary four-part log analysis: returned visible `已知事实 / 合理推断 / 未知 /
  下一步验证` sections in about 27 seconds without raw tool parameters.

The second answer still treated three 401 responses as possible brute force too
readily. This is a calibration weakness for Phase 8, not an integration failure.

## Next phase gate

Do not resume from Phase 7 merely because step 80 had the lowest validation loss.
Phase 8 should first add independently reviewed examples for evidence provenance,
false action claims, and URL re-resolution logic, then use a broader external
holdout and manual scoring rubric. No candidate should replace the active adapter
unless both the frozen suite and the Harness regression improve without new
formatting or tool-call regressions.
