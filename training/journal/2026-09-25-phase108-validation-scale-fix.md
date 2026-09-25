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

## Previously exposed empty-output sample replay prepared — 2026-09-26

- Corrected the v0.9 private-suite audit: Slurm job `44430` sampled 16 cases
  from it, so v0.9 is not an untouched blind holdout. The only prior retained
  response data are case IDs, SHA-256, and character counts; the raw prompts
  and answers remain outside Git. The original output SHA is
  `6f70e9192b019bc87ba834b903fd4f0aa972a067db1996bd080897600b8a36c6`.
- Prepared an exact-sample diagnostic replay against the parent and corrected-r2
  final adapter, using the same local-only sandbox API and sampling settings as
  job 44430. It first verifies the private source SHA
  `9a4d398893034b922cc67582089642c553733c856ab2812088b398a2546fbb6b` and the
  exact prior case-ID sequence before loading models. Output contains only
  IDs, response hashes, character counts, finish reasons, and timings; raw
  prompts/answers are never written. The job is explicitly diagnostic-only,
  unscored, and ineligible for candidate selection or promotion.
- Added replay collector
  `training/scripts/phase108_replay_diagnostic.py` and isolated Slurm job
  `training/slurm/phase108_reproduce_empty_output.sbatch`. Local Python
  compilation, CLI parsing, SBATCH syntax, and `git diff --check` pass. The
  job has not yet been submitted; scripts must be synchronized and remote hashes
  verified first. This does not change the frozen rubric/protocol or production.
- The first remote, no-model-load preflight exposed a collector bug: it checked
  `args.output.exists()` before honoring `--preflight-only`. Moved the output
  path check after preflight; no model loaded and no case was generated. The
  runner hash is now pinned as
  `c4b3744cb951f24c3d51fe087c8fb36b8953e8d7391baf3862967a56508118ea`; rerun
  local/remote preflight and hash checks before any job submission.
- Local and remote compilation now pass, the collector CLI parses, all four
  cluster code hashes match the committed sources, and the no-load preflight
  confirms the v0.9 case-source hash and exact prior 16-ID sequence. Cluster
  state before dispatch: `/data3` 280G/479G (58.5%); two existing GPU-LARGE
  jobs are pending, no user job is running, and `dell3090` is idle in
  `GPU-MEDIUM`. `sacctmgr` returned no association-limit rows. Submitting one
  bounded 1-hour GPU-MEDIUM replay job; it emits metadata/hashes only and does
  not touch production.
- Slurm job `44530` completed on `dell3090` in `00:00:56`, exit 0. It replayed
  the exact 16 previously exposed v0.9 IDs against both the pinned parent
  adapter and corrected-r2 final adapter through the same loopback sandbox API,
  base, prompt rendering, temperature, token cap, and adapter scale. Both arms
  returned 16/16 empty strings, each with the SHA-256 of empty bytes; server
  logs confirmed the correct 28-projection adapter hashes. Result JSONL SHA-256:
  parent `c2e939ac242be621f825f6d2f1bee615c3e1d4b66f3d3b9fb47d77e901d3c037`,
  candidate `8ac0ad3510a2f653808436a5f9a37f4120e9673689562d4607e9a9359a3b5ed8`,
  manifest `927a4f551b7776bf8cc5d72d87802ab32880459eefc381640f24279dd8324c29`.
  The case source and raw responses remain outside Git. This shows the empty
  output behavior on these prompts is shared by the exact parent and final
  candidate; it does not establish whether the cause is the base/template or
  the shared serving stack. Next diagnostic: same 16 messages, base-only, same
  tokenizer/template and generation settings. These known prompts remain
  excluded from blind scoring and model selection.
- Prepared base-only follow-up
  `training/scripts/phase108_base_only_replay.py` and
  `training/slurm/phase108_base_only_replay.sbatch`. The first version would
  have generated full answers; its GPU job `44535` was ours, PENDING with a
  scheduler estimate of 2026-09-30. It was cancelled before allocation/model
  load. Replaced it with a bounded CPU-only first-token diagnostic (8 CPUs,
  32G RAM, no GPU GRES, one generated token per prompt). It uses the same 16
  known messages, base, tokenizer/template, sampling controls, and fixed seed;
  it reports case IDs, response hashes/lengths, EOS status, stop reason, and
  latency only. This distinguishes base-side immediate termination from a
  possible adapter-specific effect without spending hours generating long
  answers; it is not a capability score or promotion gate.
- Base config/tokenizer and both shard hashes are pinned in the job. Local
  compile/help/shell/diff checks pass. Updated runner SHA-256:
  `3585e9f620ed43cd2d58b77a26ccd65179b21dfff0f0646d821a58fbe329f3ed`. The
  CPU-only revision still needs to be synchronized/hash-verified and its
  no-model private-source preflight run before submission. Production,
  training weights, rubric, protocol, and tools remain unchanged.

## Base-only first-token diagnostic completed — 2026-09-26

- Synchronized the CPU-only runner and SBATCH file to the cluster and verified
  hashes `3585e9f620ed43cd2d58b77a26ccd65179b21dfff0f0646d821a58fbe329f3ed`
  and `328d7323213a6e4a6bb0dcffc83b611d1270227bec0a36e67dcb668d0e74d83b`.
  Remote `py_compile`, `bash -n`, CLI help, and the no-load case-source
  preflight passed; private source SHA and the exact 16 previously exposed IDs
  matched. Disk quota remained 280G/479G (58.5%).
- Slurm job `44542` ran CPU-only on `dell3090` (8 CPUs, 32G requested, no GPU)
  and completed successfully in 53 seconds. It loaded the exact pinned base
  config, tokenizer, and both weight shards, then generated one token for each
  of the 16 known prompts. The metadata-only result reports zero first-token
  EOS events and one decoded empty string. Result JSONL SHA-256 is
  `55a19dede9949c1dc3277175ea32858d7b9df3486de1426fffd30702a0fe57f6` and is
  copied to `training/eval/phase108-v09-base-only-44542.jsonl`; raw prompt and
  answer text is absent.
- This argues against the base model immediately selecting EOS under this
  exact CPU, one-token, fixed-seed probe. It does not yet isolate the empty
  adapter outputs because the earlier loopback replay used GPU sampling with
  a continuing RNG stream and only recorded decoded text/finish reason. The
  exact 16 cases remain exposed, diagnostic-only, unscored, and ineligible for
  checkpoint selection or promotion. Production API, adapter, training
  weights, rubric, protocol, and permissions remain unchanged.

## Parent/candidate/base first-token comparison — 2026-09-26

- Added a sealed-hash-pinned, CPU-only diagnostic over the same exposed 16
  cases. Each case was evaluated once with the base, exact parent adapter, and
  corrected-r2 final adapter, using identical tokenizer/template, per-case
  seed, sampling controls, and one-token cap. The script writes only case IDs,
  token IDs/EOS flags, text hashes/lengths, and timings; no prompt/answer text.
- Slurm job `44545` completed `COMPLETED`, exit 0, in 46 seconds on `dell3090`;
  no GPU GRES was requested. Parent SHA, candidate SHA, private-source SHA,
  code hashes, and exact sampled ID sequence all passed preflight.
- Result: base `0/16` first-token EOS and `0/16` decoded-empty; parent `16/16`
  first-token EOS and `16/16` decoded-empty; corrected-r2 candidate `16/16`
  first-token EOS and `16/16` decoded-empty. Every arm generated exactly one
  token. The metadata-only JSONL SHA-256 is
  `abdde95d1aac7be71e15f999f3adaf887c0e6962dcf2daa98e43e03c471a6e63`, copied
  to `training/eval/phase108-v09-first-token-44545.jsonl`.
- This isolates the immediate-EOS behavior to the adapter-enabled path for
  this exposed diagnostic sample under the tested wrapper/settings. Since the
  exact parent and candidate behave identically, Phase108 did not introduce
  this measured failure. It does not establish behavior on unseen prompts or
  identify whether scale, adapter training targets, prompt distribution, or
  conversion semantics are the root cause. This is a blocking functional
  signal, not a benchmark score; v0.9 remains ineligible for blind scoring or
  checkpoint selection. Next, run a metadata-only scale sensitivity probe on
  this exposed sample before making any training or serving change.
- No production API/adapter, model weights, evaluation rubric/protocol, or
  tool permission changed.

## Exposed-sample adapter-scale sensitivity — 2026-09-26

- Job `44547` ran a CPU-only, 160-row first-token probe on the same 16 exposed
  case IDs: parent and corrected-r2 candidate, each at fixed scales 0, 2.5, 5,
  10, and 20. It completed on `dell3090` in 78 seconds with exit 0 and no GPU
  GRES. Adapter, base-independent case source, and script hashes passed the
  remote preflight; the output contains only IDs/token IDs/hashes/lengths and
  metadata, no prompt or answer text.
- EOS counts at scales 0 / 2.5 / 5 / 10 / 20 were **0 / 0 / 0 / 2 / 16** for
  both parent and candidate (16 prompts per scale). At scale 0, both adapter
  wrappers matched the base's non-EOS first-token behavior. Metadata JSONL SHA:
  `fe4acb5b0b3c065b82ab26e67d0d09ce81c24b8315b973547c33565b01eab3a7`, copied
  to `training/eval/phase108-v09-scale-sensitivity-44547.jsonl`.
- The strong scale association makes scale/wrapper semantics a leading cause
  to investigate, but does not prove scale 5 is a valid operating point or
  preserve specialist performance. No scale is being changed in production or
  selected from this exposed sample. A follow-up 16-token-capped diagnostic
  is prepared to see whether reduced scales produce any short visible text;
  it remains functional-only and cannot substitute for fresh blind evaluation.

## Exposed-sample 16-token scale diagnostic completed — 2026-09-26

- Slurm job `44550` completed on `dell3090`, exit 0, elapsed `00:13:39`;
  CPU-only allocation (4 CPUs/20G, no GPU GRES). The remote runner and SBATCH
  hashes matched the committed/pinned values
  (`9edb367ba8255c86164c87e61dd0f6e283e211d78899a4191c3676284758833b` and
  `6d69522d979d6121e2ab126144c4e52d28ce514c7a4d622c80a31198395bfd59`).
  Preflight reports expected input hashes and selected exposed IDs matched.
- The 160 metadata records cover the same 16 already-exposed v0.9 cases for
  exact parent (`3ed1a85e7b021e1498332a525bfa4bb75b336a03579d526f8210f1576317036`)
  and corrected-r2 final candidate
  (`4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`) at
  scales 0, 2.5, 5, 10, and 20. No prompt or answer text is present. Remote and
  local result SHA-256 both equal
  `06512ee70a87da55f4eb2ce6d56223f5aca513694810c90374d13771bf7254d1`.
- For both parent and candidate, first-token EOS/decoded-empty counts were
  0/16 at scales 0, 2.5, and 5; 2/16 at scale 10; and 16/16 at scale 20.
  At scales 0–5 every sample generated the full 16-token cap, so “non-empty”
  here only means visible tokens before truncation; response quality was not
  assessed. At scale 10, the two EOS cases stopped at token 1; the remaining
  fourteen reached the cap. At scale 20, all stopped immediately at EOS.
- This strengthens the observed association between adapter scale and early
  termination on this *exposed diagnostic sample*, and shows the exact parent
  and candidate have the same pattern. It does not identify the underlying
  mechanism, prove reduced-scale specialist capability, or justify changing
  inference scale. No score, blind claim, candidate selection, or promotion
  decision is made. The metadata-only result is stored at
  `training/eval/phase108-v09-scale-sensitivity-44550.jsonl`; raw responses
  remain outside Git. Production, rubric/protocol, and permissions are
  unchanged.

## Earlier bare-canary scale evidence reconciled — 2026-09-26

- Rechecked the separate 100%-bare canary adapter at SHA-256
  `5686ee98e8ed09cd31f3f0228dd4cfec60fd58907090b5ec71372c83571f7da4`; the
  cluster adapter file and all four isolated sandbox readiness logs agree on
  that hash. This is **not** the corrected-r2 adapter tested by jobs 44542–44550.
- On the already-exposed v0.9 sample, job `44462` had 0/16 non-empty responses
  at the diagnostic default scale 20; scale-zero control `44463` had 16/16
  non-empty. The same adapter returned 16/16 non-empty in the scale-1 and
  scale-2.5 compatibility probes (`44467`, `44468`).
- The separate 320-row response-collection job `44473` used that same bare
  adapter at scale 1 and recorded 319/320 non-empty responses. Slurm confirms
  `COMPLETED`, exit 0, elapsed `00:45:57`; its metadata-only result SHA-256 is
  `f1fd9ddb1e68ff53f8b50be234cccbbcaad7b04dc1faa44eb40b380d78c878f5`. It
  stores only case IDs, response lengths, empty flags, and response hashes—not
  answer text—and is not a scored evaluation.
- These historical diagnostics are consistent with adapter-scale-sensitive
  termination, but they use a different candidate and the now-exposed v0.9
  suite. They cannot establish quality at scale 1 or candidate capability.
  v0.9 remains disqualified as a blind holdout. No inference scale, adapter,
  model/API, rubric, protocol, or permissions changed.

## Current cluster recheck — 2026-09-26

- Reconnected to the CUHK login node using the existing SSH identity and
  checked `squeue`/`sacct` plus the candidate directory. There are no Phase108
  training or evaluation jobs currently pending/running. Training job `44306`
  is recorded as `COMPLETED`, exit `0`, elapsed `01:01:25` on `a100-1`.
- Recomputed SHA-256 for the final corrected-r2 adapter:
  `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`.
  This matches the manifest, training log, prior fixed-validation report, and
  prior behavioral diagnostics. All numbered snapshots 1,000 through 7,000
  were present and had distinct recorded hashes; the final adapter is the
  exact artifact used by jobs 44430 and 44530.
- Candidate manifest records the sealed Phase108 step-12,000 input adapter
  SHA, rank 8, MLX scale 20, PEFT alpha 160, effective scale 20, and
  `test_split_read=false`. Fixed validation job `44518` evaluated all 1,089
  frozen validation rows for eight numbered snapshots and final weights with
  those scale fields; the lowest loss was final weights at `1.7062584871`.
- This loss result does not clear the behavior gate: the exact parent and
  corrected-r2 adapter both emitted immediate EOS on all 16 already-exposed
  v0.9 diagnostic prompts at scale 20, while the base-only arm did not. Scale
  0/2.5/5 suppressed immediate EOS on that exposed sample, but quality was not
  measured, so no inference scale is selected from it.
- The latest independent scenario audit rejects v0.8 as 320 independent cases
  because it repeats 40 core motifs across eight strata. v0.9 was previously
  exposed and is not a blind holdout. Therefore no fresh blind score or
  checkpoint promotion is supported. The next gate is a materially distinct
  replacement suite plus contamination and independent semantic review; do
  not submit another behavior evaluation until that gate is met.
- `/data3` was 280G/479G (58.5%), below the repository's 95% stop threshold.
  Production API, adapter, benchmark rubric/protocol, and tool permissions
  remain unchanged.
