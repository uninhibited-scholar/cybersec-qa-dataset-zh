# Phase 108 post-training gates

This runbook is for the isolated `phase108-cleanv2-epoch1-20260920` candidate only. It does not authorize a production change, a tool-permission change, a rubric change, or a test-set-driven checkpoint selection.

## Preconditions

1. Confirm the Phase 108 MLX process has exited normally. Do not infer from a checkpoint alone that training is complete.
2. Preserve the immutable candidate directory, training log, numbered checkpoint hashes, adapter config, frozen Phase 107 manifest hash, answer-key hash, and frozen validation-file hash.
3. Run `phase108_checkpoint_report.py` after process exit. It must report no inventory errors. The report's in-training validation losses are not selection scores.
4. Confirm the active production service still uses its pre-existing model and adapter paths; do not stop, reload, or replace it.

## Checkpoint selection: fixed validation only

For every numbered, matched checkpoint listed by the final checkpoint inventory:

1. Run `phase108_common_validation.py` with the frozen 1,089-row `valid.jsonl`, its recorded SHA-256, the matching base model path, `mask_prompt=True`, max sequence length 2,304, and seed 20260920.
2. Keep the generated JSON manifests. A run is invalid if the validation hash, adapter/base association, truncation check, checkpoint stability check, or finite-loss check fails.
3. Do not load the test split during checkpoint selection.
4. Select only using the common-validation results. Record all evaluated checkpoints, not only the winner.

## Candidate behavior gates

The selected candidate stays isolated. Before any promotion recommendation it must pass all of the following:

1. Phase 107 output collection using the frozen v0.2 manifest, rubric v0.1, inference protocol v0.1 and approved corrigendum v0.1.1.
2. The exact same messages, no-tool instruction, empty tool inventory, output ceiling, sampler controls where exposed, timeout accounting, and parser behavior used by Phase 91 and each reference arm.
3. Blind labels for candidate, Phase 91, and at least two reference models. Do not provide answer keys to any model request.
4. Per-stratum reporting across vulnerability analysis, detection/remediation, threat modeling, code review, evidence boundaries, multi-turn reasoning, tool honesty, and prompt injection.
5. Explicit reporting of empty outputs, truncation, transport errors, latency, finish reason, unsupported claims, hallucination findings, format failures, and permission/tool-honesty failures.
6. Independent semantic calibration and blind critical-failure adjudication. Automated keyword/loss checks are insufficient.
7. A rollback check: candidate inference must use its own adapter path and the known matching base, with no write to the production adapter, production service, rubric, or evaluation manifest.

## Promotion boundary

Passing the gates produces an evidence package and a recommendation only. The candidate may enter personal production only after the user explicitly approves that exact candidate/version. No process in this workflow can approve itself, enlarge tool access, change scoring rules, or replace the Phase 91 service.
