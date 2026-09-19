# Phase 107 replacement benchmark — draft

This is a design draft only. It does not alter the Phase 104 scoring rule or start a model run.

## Acceptance criteria

1. At least 320 cases: 40 each for vulnerability analysis, detection/remediation, threat modeling, code review, evidence boundaries, multi-turn reasoning, tool honesty, and prompt injection.
2. Every case must have a distinct underlying system, artifact, or decision. Different IDs, numbers, or boilerplate prefixes do not count as independent cases. Automated deduplication must be followed by a manual scenario-family audit.
3. Store prompt cases separately from answer keys. Each key defines required facts, unsupported claims to avoid, evidence requirements, and output constraints.
4. Scan prompts, fixtures, and keys against every local train/valid/test and historical-eval source. Record hashes and exclusions. Exact and normalized checks are minimum gates, not proof against foundation-model pretraining exposure.
5. Keep all cases defensive and offline; no live targets, executable attack workflows, or tool access.
6. Freeze one new rubric version before scoring any model. Keep it separate from the unchanged Phase 104 rubric. Automated checks cover only objective constraints; human semantic adjudication is needed for correctness and critical failures.
7. Blindly label model outputs. Run Phase 91, at least two references, and any candidate against the same prompts, conversation context, effective no-tool system instruction, empty tool inventory, output ceiling, timeout, and response parser. Use common sampler controls where the API exposes them; record all model-specific decoding, seed, reasoning-mode, retry, and post-processing behavior rather than claiming exact parity when it is unavailable. The primary Phase 91 arm is the deployed endpoint, including its guards/retries; label results as end-to-end system comparisons. A raw-weight comparison requires a separate wrapper-free protocol. Record latency and finish reason; provider/model reasoning settings must be explicit and visible-reasoning output must be handled consistently.
8. Report per-stratum metrics, macro-average, uncertainty, empty/truncated/transport failures, and human-adjudicated results. No candidate promotion based only on loss or keyword scores.

## Case schema (draft)

Prompt manifest rows contain `id`, `stratum`, `messages`, `fixture_hash`, `provenance`, and `rubric_ref`. Single-turn rows use one user message; multi-turn rows use an explicit ordered conversation (including the same fixed prior assistant turn for all systems). The original `prompt` field is retained only as an auditable source representation; the runner must treat `messages` as authoritative and must not concatenate both. A separate private answer-key file contains `must_cover`, `must_not_claim`, `evidence_boundary`, and `format_contract`. Do not include answer keys in model requests.

## Method references

- [Meta CyberSecEval 4](https://github.com/meta-llama/PurpleLlama/tree/main/CybersecurityBenchmarks): taxonomy/method reference for secure-code, prompt-injection, interpreter safety, and defensive SOC evaluations. Its public items are not a private uncontaminated holdout; operationally offensive subsets are out of scope.
- [SEC-bench](https://github.com/SEC-bench/SEC-bench): agent-oriented real software vulnerability and patching evaluation; a future complementary benchmark requiring a more substantial Docker/repository environment.
- [NIST SSDF SP 800-218](https://csrc.nist.gov/pubs/sp/800/218/final): defensive remediation criteria source, not a labeled test set.

Public-benchmark runs and the private held-out suite must be scored/reported separately.

## Status

Draft, not scored. The local-only v0.2 320-case candidate bank has 40 items per stratum, separate answer keys, and actual user/assistant/user turns for its 40 multi-turn cases. Generation, targeted diversity, and exact-overlap checks pass, but the rubric/protocol remain unfrozen and no model was queried. Phase 104/106 remain historical diagnostic evidence only; Phase 91 production is unchanged.

The candidate bank and keys are gitignored. The reproducible builder and aggregate audit are tracked; hashes are recorded in `phase107-private-suite-audit.md`. Exact-overlap checks cover the scanned local JSONL scope only and do not establish semantic or pretraining cleanliness. No parity or model-quality claim may be made from this draft.
