# Phase 107 replacement benchmark — draft

This is a design draft only. It does not alter the Phase 104 scoring rule or start a model run.

## Acceptance criteria

1. At least 320 cases: 40 each for vulnerability analysis, detection/remediation, threat modeling, code review, evidence boundaries, multi-turn reasoning, tool honesty, and prompt injection.
2. Every case must have a distinct underlying system, artifact, or decision. Different IDs, numbers, or boilerplate prefixes do not count as independent cases. Automated deduplication must be followed by a manual scenario-family audit.
3. Store prompt cases separately from answer keys. Each key defines required facts, unsupported claims to avoid, evidence requirements, and output constraints.
4. Scan prompts, fixtures, and keys against every local train/valid/test and historical-eval source. Record hashes and exclusions. Exact and normalized checks are minimum gates, not proof against foundation-model pretraining exposure.
5. Keep all cases defensive and offline; no live targets, executable attack workflows, or tool access.
6. Freeze one new rubric version before scoring any model. Keep it separate from the unchanged Phase 104 rubric. Automated checks cover only objective constraints; human semantic adjudication is needed for correctness and critical failures.
7. Blindly label model outputs. Run Phase 91, at least two references, and any candidate against the same prompts, context, system instructions, empty tool inventory, output-token budget, temperature, retries, timeout, and parser. Record latency and finish reason. Provider-specific thinking modes must be a separately reported condition.
8. Report per-stratum metrics, macro-average, uncertainty, empty/truncated/transport failures, and human-adjudicated results. No candidate promotion based only on loss or keyword scores.

## Case schema (draft)

Prompt manifest rows contain `id`, `stratum`, `prompt`, `fixture_hash`, `provenance`, and `rubric_ref`. A separate private answer-key file contains `must_cover`, `must_not_claim`, `evidence_boundary`, and `format_contract`. Do not include answer keys in model requests.

## Method references

- [Meta CyberSecEval 4](https://github.com/meta-llama/PurpleLlama/tree/main/CybersecurityBenchmarks): taxonomy/method reference for secure-code, prompt-injection, interpreter safety, and defensive SOC evaluations. Its public items are not a private uncontaminated holdout; operationally offensive subsets are out of scope.
- [SEC-bench](https://github.com/SEC-bench/SEC-bench): agent-oriented real software vulnerability and patching evaluation; a future complementary benchmark requiring a more substantial Docker/repository environment.
- [NIST SSDF SP 800-218](https://csrc.nist.gov/pubs/sp/800/218/final): defensive remediation criteria source, not a labeled test set.

Public-benchmark runs and the private held-out suite must be scored/reported separately.

## Status

Draft. No Phase 107 prompts have been accepted or run. Phase 104/106 remain historical diagnostic evidence only; Phase 91 production is unchanged.
