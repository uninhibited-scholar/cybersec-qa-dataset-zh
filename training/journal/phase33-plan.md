# Phase 33 plan

## Starting point

Use `phase31-focused-20260916` as the read-only starting adapter. Do not resume from Phase 32 because its short cyber answers regressed to generic fallback.

## Scope

- Add only a small, user-authored style set covering concise SQL/XSS/command-injection explanations, evidence-qualified history answers, and pure-Chinese terminology.
- Keep the original clean cyber dataset as the overwhelming majority of training data.
- Use a low learning rate and short run with checkpoints; never overwrite prior adapters.

## Gates

1. No empty answers on the short cyber holdout.
2. Short answers retain concrete domain content, not generic fallback text.
3. Strict JSON and one-token formats remain exact.
4. Unsupported CVE/history claims remain evidence-qualified.
5. Tool-positive outputs retain provenance; tool-negative outputs do not claim execution.
6. Ordinary questions remain answerable.
7. Candidate remains isolated until authenticated API regression and human approval.

## Rollback

Any failed gate rejects the candidate and leaves Phase 31 (plus the production adapter) untouched.
