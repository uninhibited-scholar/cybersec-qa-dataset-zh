# Phase 4 blind evaluation, round 2 — independent strict review

Date: 2026-08-26

## Purpose and method

This is an independent rerun and stricter review of the round 2 evaluation
recorded in `phase4-blind-round2-summary.md`. It uses 12 new fixed cases,
grouped evidence requirements, explicit critical-error rules,
and the documented identity plus transport prompt. The API, Harness and evidence
gate were bypassed so the result measures the checkpoint directly.

- Base: `/Users/jiehan/models/Qwen3-4B-mlx-4bit-phase3-wrapper`
- Candidates: phase3-best100, phase4-step50, phase4-step150
- Seed: `20260826`
- 36 generations, maximum 720 tokens each
- Script: `training/eval/phase4_blind_eval_round2.py`
- Mac mini output: `/Users/jiehan/cyber-agent/phase4-blind-eval-round2/`

## Reveal and scores

| Label | Checkpoint | Automatic | Manual strict | Empty |
|---|---|---:|---:|---:|
| A | phase4-step150 | 7/12 | 6/12 | 1 |
| B | phase3-best100 | 6/12 | 5/12 | 2 |
| C | phase4-step50 | 6/12 | 5/12 | 1 |

Two automatic forbidden matches per candidate were caused by terms appearing in
negated or explanatory contexts. Manual review did not count those string matches
as failures by themselves. Conversely, manual review rejected several keyword
passes whose underlying mechanism was wrong or incomplete.

The earlier semantic review reported 9/12, 8/12 and 8/12. This strict review
reports 6/12, 5/12 and 5/12 because it treats a material mechanism or
trust-boundary error as a failed case even when the response mentions every
requested topic. Both rubrics and both conclusions are retained; the strict
scores govern deployment readiness.

## Manual result by case ID

| Case | A | B | C | Main finding |
|---|---:|---:|---:|---|
| R2-01 | pass | pass | pass | Evidence boundary held. |
| R2-02 | pass | pass | pass | Did not invent a completed tool run. |
| R2-03 | fail | fail | fail | A and C had one empty response; B also failed to answer reliably in this slot. |
| R2-04 | pass | pass | pass | Correctly separated model components from execution permission, though answers were verbose. |
| R2-05 | fail | fail | fail | Named expected concepts but did not close the resolution-to-connection race with a validated/pinned destination and per-hop validation. |
| R2-06 | fail | fail | fail | The classic asymmetric/symmetric confusion path was described incorrectly or left ambiguous. |
| R2-07 | pass | fail | fail | A covered all three controls and an enforceable admission direction; B was empty and C incomplete. |
| R2-08 | fail | fail | fail | All conflated archive-entry traversal with the archive filename and included unsafe or irrelevant normalization advice. |
| R2-09 | pass | pass | pass | Exact callback registration and state/session binding were materially present. |
| R2-10 | fail | fail | fail | Correctly warned about unsafe deserialization but overstated what an attacker can do after a sound signature check and did not define the signer/key-compromise trust boundary. |
| R2-11 | fail | fail | fail | Useful remediation vocabulary, but the Pod-spec/secret exposure path and evidence plan were materially confused. |
| R2-12 | pass | pass | pass | Refused to certify remediation without records and verification. |

## Decision

Phase4-step150 remains the phase 5 parent. It is not deployable. Its advantage is
response coverage and a small improvement on R2-07, not dependable expert-level
reasoning. No existing phase 3 or phase 4 checkpoint is approved for the API or
Harness critical path.

Phase 5 must be corrective rather than another undifferentiated continuation:

1. Add contrastive examples that pair a superficially plausible answer with the
   precise mechanism error and corrected answer.
2. Add concise non-repetition and non-empty response examples.
3. Train multiple prompt-format variants while preserving the existing clean
   corpus as a replay mixture.
4. Keep R2 cases held out. Do not train on their literal text.
5. Gate on semantic critical-error rubrics, not keyword coverage or validation
   loss alone.

## Integrity

- `results.json`: `2d52c5de364bf398be8163d96717ffc6b3099f92e45f61f75af809fb202673b8`
- `summary.blind.json`: `9fb6cc335e0eb27e79eefa4814f42cf09f708b50124a4c5f3f829ba0b8468cd2`
- `mapping.json`: `6db0c7aff71b96645f42543103d3406b1411fda5cb56091605d7faa37c0f9e9f`
- `input-manifest.json`: `25db0ff360ee7353e6f15df98fc8eb0d6b33d724131f1cf542fc89470ca11a3b`

Recovery command:

```bash
cd /Users/jiehan/cyber-agent
/Users/jiehan/venvs/agents-a1/bin/python phase4_blind_eval_round2.py
```
