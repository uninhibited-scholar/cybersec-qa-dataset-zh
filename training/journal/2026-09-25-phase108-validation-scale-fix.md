# Phase108 fixed-validation scale correction

Date: 2026-09-25

## Finding

An audit of Slurm job 44429 found that the fixed-validation runner installed a
rank-8 adapter with `lora_alpha=20`, giving PEFT an effective multiplier of
`20 / 8 = 2.5`. The candidate manifest records MLX direct scale 20 and PEFT
alpha 160. Therefore job 44429's loss (`2.030983971115424`) is not a valid
fixed-scale checkpoint-selection result and is withdrawn from comparison; its
validation data read itself was still restricted to the frozen 1,089-row
`valid.jsonl` (SHA-256
`44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365`).

## Artifact identity

- Candidate run: `phase108-cuda-recovery-scale20-corrected-20260924-r2`.
- No-inference provenance preflight passes with the directly verified input
  adapter SHA-256 `3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`.
- The run manifest records rank 8, MLX scale 20, PEFT alpha 160, effective
  scale 20, 19,621 training rows, and `test_split_read=false`.
- The prior blind-smoke checkpoint `0007000_adapters.safetensors` has SHA-256
  `62acbdc57011ea5a4927514c6868549d98ae36501ddbefab847424cb4ebe66ed`.
- The run's final `adapters.safetensors` has SHA-256
  `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`.
- Job 44430 tested the numbered step-7000 checkpoint at direct inference
  scale 20 and returned empty text for all 16 diagnostic prompts. This remains
  a functional failure signal, not a capability score.

## Correction and next evaluation

- Added a shared, dependency-light `mlx_scale_to_peft_alpha` helper so CUDA
  training and fixed validation use the same scale conversion.
- Fixed validation now explicitly reports requested MLX scale, rank, PEFT
  alpha, and effective scale. It keeps the same base, tokenizer, validation
  data/hash, full-row coverage, masking, maximum length, and loss definition.
- A pinned sweep covers steps 1, 1000, ..., 7000 and final weights; every
  checkpoint SHA, runner SHA, base-config SHA, input-adapter SHA, and validation
  SHA is checked before evaluation. Only the validation split is read; no
  generation outputs are emitted or stored.
- Sweep job `44517` started at `2026-09-25T23:49:58` on `dell3090` (GPU-MEDIUM).
  Its no-inference scale preflight passed. The base shard SHA-256 values
  observed inside the allocation are `model-00001-of-00002.safetensors`:
  `25094f7fbaef4769da447cb6ebf4a39d99ccc5043856cce1b4f8fc2f91ed9115` and
  `model-00002-of-00002.safetensors`:
  `a2fd70328fc4fb518bb40ac806e8c05f21ad12e228648684775f67c28104815d`.
  Result JSONL is expected at
  `results/phase108-r2-fixed-scale-validation-44517.jsonl`; the Slurm log is
  `logs/phase108-r2-valscale20-44517.log`.
- Job 44517 then failed after 1:07 before producing any validation metric:
  its loader expected `model.layers.*`, while this candidate serializes keys as
  `layers.*`. The result path exists but is empty (0 bytes) and is retained as
  a failure artifact. The base model was loaded before this key mismatch was
  noticed. The evaluator now normalizes both supported prefixes, validates
  28 A/B projection pairs and layer topology before loading the multi-GB base,
  and has unit coverage for key normalization and PEFT destination mapping.
  Corrected runner and helper hashes are pinned in a new job submission; no
  validation score from 44517 is usable.
- Corrected retry `44518` started at `2026-09-25T23:57:31` on `dell3090`.
  The normalized-key preflight passed and the base shards loaded; at the latest
  check (1:55 elapsed) it remained RUNNING with no checkpoint-level JSON metric
  written yet. Its unique output path is
  `results/phase108-r2-fixed-scale-validation-44518.jsonl`.
- At 5:02 elapsed, the first complete record (step 1) was written with adapter
  SHA-256 `7f1024dc51019a7114dfa32874b41f513161b3aff59756e59c3f49725ec22759`,
  validation loss `1.736240570593362`, 1,089 rows, effective scale 20.0, and
  train/test split access both false. The job remained RUNNING and had moved to
  the next checkpoint; no selection decision is made until all records and
  final hashes are verified.
- This correction does not change the Phase107 inference protocol or rubric.
  It corrects a training/selection-time scale mismatch. No checkpoint is
  selected from the invalid 44429 metric.
- The v0.9 private suite has already been used diagnostically and is not a
  pristine promotion holdout. A fresh independent blind suite remains required
  after candidate selection and semantic-freshness review.

## Deployment and isolation

Production API, Phase91 adapter, evaluation rubric/protocol, and tool
permissions remain unchanged. Candidates remain in the isolated sandbox.

## Corrected full fixed-validation sweep completed — 2026-09-26

- Slurm job `44518` finished `COMPLETED`, exit `0`, elapsed `00:25:24` on
  `dell3090`. The remote result has 9 records; its SHA-256 is
  `7a0d59d5b9119270693a680bfd5d7ff5e4f74864f12fff546be854404ef08ade`.
  The byte-identical local copy is
  `training/eval/phase108-r2-fixed-scale-validation-44518.jsonl`.
- Every row reports rank 8, MLX scale 20, PEFT alpha 160, effective scale
  20.0, 1,089 validation rows, frozen validation SHA-256
  `44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365`, and
  `train_split_read=false`, `test_split_read=false`,
  `production_approval=false`.
- Results by checkpoint (validation loss; lower is better): step 1
  `1.7362405706`; 1000 `1.7315177635`; 2000 `1.7267208465`; 3000
  `1.7226179229`; 4000 `1.7186481314`; 5000 `1.7152950378`; 6000
  `1.7118153573`; 7000 `1.7081212176`; final adapter `1.7062584871`.
  The lowest measured loss is the final adapter SHA-256
  `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`.
- This repairs the invalid-scale measurement and establishes a monotonic
  validation-loss trend within this run. It does **not** establish a gain
  over the exact parent adapter, Phase91/production, or another model family;
  loss is not behavioral quality. The earlier 16/16 empty-text smoke signal
  at step 7000 remains an unresolved functional failure signal. No checkpoint
  is selected for promotion, and no model/API/adapter, rubric, protocol, or
  tool permission was changed.
- Next: compare the exact Phase108 input adapter and final candidate under the
  same fixed validation implementation; then use a fresh, contamination-audited
  blind holdout and full functional/security gates. Keep serving-model family
  selection independent: the Phase108 adapter is Qwen-specific, but the
  cluster's API/Harness need not be.
- To establish the direct parent baseline before judging the continuation,
  submitted isolated Slurm job `44521` on 2026-09-26. It evaluates only the
  exact Phase108 input adapter (SHA-256
  `3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`) on the
  same frozen 1,089-row validation split, same base, runner, sequence limit,
  and effective LoRA scale 20. The first attempt failed at its pinned SHA
  preflight due to a transcription typo in the job script, before model load
  or inference; it emitted no result. The log identified expected-vs-observed
  hash mismatch, and the exact remote parent/manifest hashes were independently
  rechecked. A one-minute Slurm GPU diagnostic (44522) passed on `dell3090`
  with `CUDA_VISIBLE_DEVICES=0` and visible RTX 3090, ruling out node/GPU
  allocation as the cause. The committed job file is
  `training/slurm/phase108_parent_fixed_validation.sbatch` (SHA-256
  `17fc4ca7891e5ba7c05b33692d4e19cd3bed57fcc75921b31e55cabc6d1be652`). A
  second attempt (44523) confirmed the same preflight typo and also produced no
  inference/result. The corrected script SHA-256 is
  `a5a6674f50023788decdda9e14fa45fb7b49ff318fbece0af68fce988184a7f1`;
  corrected job `44525` started on `dell3090` and passed all pinned artifact,
  config, and data preflights before loading the base. Its result path is
  `results/phase108-parent-fixed-scale-validation-44525.jsonl`. This is a
  validation-loss baseline only, not a behavioral score or promotion decision.

## Exact parent baseline completed — 2026-09-26

- Job `44525` completed on `dell3090` with exit code `0` in `00:03:39`; its
  output contains exactly one complete record. Remote and local JSONL SHA-256:
  `a68e6b69f224ac51c0200ecd37bab9fa28b89dd781002d4250753dbc30423a5c`.
- The row verifies the exact parent adapter SHA-256
  `3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`, rank
  8, MLX scale 20, PEFT alpha 160/effective scale 20, validation SHA-256
  `44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365`, 1,089
  rows, `train_split_read=false`, and `test_split_read=false`.
- Exact parent full-validation loss is `1.7362299831336085`. Against the
  corrected-r2 final adapter's `1.7062584870555622`, this is an absolute
  reduction of `0.0299714960780463` (about 1.73% relative). The split, base,
  runner, token limit, LoRA rank/scale, and masking are matched. This supports
  a lower held-out token loss for this specific source split, but not improved
  generation, security-task capability, or deployment readiness. The separate
  step-7000 16/16 empty-output diagnostic remains a blocking functional signal.
- Result copy committed at
  `training/eval/phase108-parent-fixed-scale-validation-44525.jsonl`; the
  previous zero-result failed jobs 44521 and 44523 remain documented and were
  not mistaken for model results. Production API/adapter, rubric, protocol,
  and tool permissions remain unchanged.

## Public functional diagnostic queued — 2026-09-26

- To investigate whether the empty-output signal is specific to the previously
  sampled private prompt forms, submitted Slurm job `44527` for a sequential,
  tool-free comparison of the exact parent adapter and corrected-r2 final
  adapter on four fixed public-development probes. This is explicitly not a
  blind benchmark, score, or promotion gate.
- Both arms use the same local base, tokenizer/template, `phase108_cuda_diagnostic.py`,
  `phase108_hf_adapter_smoke.py`, BF16 setting, deterministic decoding, and
  96-token cap. The pinned parent SHA is
  `3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`; the
  corrected-r2 final SHA is
  `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`.
- Committed Slurm script SHA-256:
  `acc5a2d8cc2ec91f3dd8a148f2aeb7cbdb0a389dfd69201eec29a4647a8b8cc7`.
  Raw outputs are mode-restricted under the unique remote directory
  `results/phase108-public-diagnostic-44527/` and must stay outside Git. Only
  hashes and non-textual aggregate findings may be committed. Production,
  benchmark rubric/protocol, blind-suite artifacts, and tool permissions are
  unchanged.
- Follow-up on 2026-09-26: Slurm reports `44527` as `FAILED`, exit `1:0`,
  elapsed 25 seconds. The pinned parent/candidate public diagnostic produced no
  generations: the shared diagnostic runner passed `dtype=` to this installed
  Transformers/Qwen3 loader, whose constructor rejected it. This is a runner
  compatibility failure, not evidence about either model. No output files were
  present. Do not retry until the runner is patched and locally preflighted;
  production and evaluation settings remain unchanged.
- Repair: changed the diagnostic loader to the `torch_dtype=` spelling used by
  the already exercised Phase108 CUDA adapter smoke loader, and enabled
  `low_cpu_mem_usage=True`. Local Python compilation, SBATCH shell syntax, and
  `git diff --check` pass. The runner source SHA-256 is
  `2ce538b6f70d00fe407894c7516a648bf84ab78032dc1c3c9e8b4d9f53be855c`; the
  SBATCH script pins this exact hash. This is an infrastructure repair only;
  no model weights, data, prompts, rubric, protocol, or production state changed.
- Re-copied the repaired runner and SBATCH script to the cluster and verified
  their SHA-256 values match Git; remote `py_compile` passed. Confirmed the
  pinned parent and corrected-r2 adapter hashes still match their expected
  values, failed-run output directory had no generation files, and `/data3`
  usage is 280G/479G (58.5%). Resubmitted only the isolated public-development
  diagnostic as job `44528`; it is not blind evaluation or a promotion gate.
- Job `44528` completed on `dell3090` in `00:01:18`, exit 0. The exact parent
  and corrected-r2 candidate each produced 4/4 non-empty, uncapped outputs on
  the same public probes (geography, exact JSON, tool honesty, and a
  parameterized-query concept). Both returned the expected city/JSON shape and
  honestly declined to invent unavailable server logs; their defensive concept
  explanations were substantively similar. Per-row adapter SHA checks passed
  for both arms. Output SHA-256 values: parent
  `d6051ac792daa0e74b0e156051d84a62610144a554e19613d8ed32196958982b`, candidate
  `285fcf0ab0009bbde41a874f1043c689b527ee2ccf89ca263026d4033a4f2dca`, manifest
  `62d30f8e4209ff5771bcae962660fc4299a2778fb5ce61e76a6882594f4a5b83`. Raw
  responses stay on the cluster outside Git. This small public diagnostic
  contradicts a universal empty-generation failure, but does not reproduce or
  explain the earlier 16/16 empty results on the sealed v0.9 prompt forms and
  cannot establish capability gain, independent blind performance, or
  deployment readiness. No model, API, rubric, protocol, or permissions changed.
