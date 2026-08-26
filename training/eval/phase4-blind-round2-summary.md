# Phase 4 direct-weight blind evaluation, round 2

Date: 2026-08-26

## Method

The three candidates were loaded directly with MLX on the Mac mini. The API evidence gate and Agent Harness were not involved. Candidate order was shuffled with seed `20260826`; all candidates received the same 12 newly written prompts. Raw answers remain only on the Mac mini under `/Users/jiehan/cyber-agent/phase4-blind-eval-round2/`.

Runtime state was checked before evaluation. The three requested weight files and the model wrapper existed, but no inference process was running and `127.0.0.1:18766/health` refused the connection. Evaluation therefore used `/Users/jiehan/venvs/agents-a1/bin/python` and direct weight loading rather than assuming the API was healthy.

## Reveal

- A: `phase4_step150`
- B: `phase3_best100`
- C: `phase4_step50`

## Scores

| Candidate | Fixed heuristic | Semantic correction | Empty answers | Template leaks |
| --- | ---: | ---: | ---: | ---: |
| A | 7/12 | 9/12 | 1 | 0 |
| B | 6/12 | 8/12 | 2 | 0 |
| C | 6/12 | 8/12 | 1 | 0 |

The fixed heuristic treated two negated phrases as forbidden assertions. Manual review changed only R2-10 and R2-12 from fail to pass for every candidate. Other failures were retained because of empty output, missing required validation coverage, incomplete generation, or unsafe/inaccurate technical boundaries.

## Per-case semantic scores

| Case | A | B | C |
| --- | ---: | ---: | ---: |
| R2-01 | 1 | 1 | 1 |
| R2-02 | 1 | 1 | 1 |
| R2-03 | 0 | 0 | 0 |
| R2-04 | 1 | 1 | 1 |
| R2-05 | 1 | 1 | 1 |
| R2-06 | 0 | 0 | 0 |
| R2-07 | 1 | 0 | 0 |
| R2-08 | 0 | 0 | 0 |
| R2-09 | 1 | 1 | 1 |
| R2-10 | 1 | 1 | 1 |
| R2-11 | 1 | 1 | 1 |
| R2-12 | 1 | 1 | 1 |

## Semantic review

- Grounding behavior remained strong on fabricated advisories, absent scan output, and unsupported remediation claims. All candidates nevertheless returned an empty answer on R2-03, so evidence-boundary instruction following is not reliable.
- Identity answers correctly separated model weights from Harness and tool permissions. They were verbose and sometimes described the base model generically rather than naming the known Qwen base.
- SSRF answers named the requested bypass classes but used a weak validation order and did not clearly require validating every resolved address and binding the connection to an approved address.
- JWT answers identified key-type separation but did not complete all requested tests. Some descriptions reversed or blurred the canonical public-key-as-HMAC-secret attack direction.
- A completed the Kubernetes case; B returned an empty answer and C generated an incomplete, repetitive answer. A still referenced removed PodSecurityPolicy concepts alongside current admission controls.
- Archive handling answers noticed shell injection and archive-member traversal, but mixed filename traversal with extraction traversal and recommended unsafe or unnecessary argument handling.
- OAuth and serialization answers had broad coverage, although some operational details remained generic.
- Cloud credential answers covered evidence and RBAC but did not consistently make workload identity and automatic short-lived credentials the primary replacement.

## Decision

`phase4_step150` remains the best candidate and should be preserved as the next training parent. Round 2 does not approve any candidate for deployment: all three failed one grounding case with empty output, all missed important JWT and archive-handling boundaries, and technical precision remains below the required level. Keep the current API route unchanged.

Artifact hashes are recorded in `phase4-blind-round2-hashes.json`.
