# Phase 108 data and lineage preflight — 2026-09-20

## Decision

Do not resume training from Phase 94/95 correction files: they add little or no new input coverage beyond the current Phase 91 lineage, and their validation/test splits contain exact prompt overlap with training. The primary user dataset `cybersec-clean-v2` is a better next training source: its train/validation/test prompt sets are exactly disjoint in the scanned files and it has no exact normalized prompt overlap with the known historical datasets in the active lineage. This is an exact-string result, not a semantic-contamination certification.

## Current production lineage

- Live Phase 91 service remains unchanged on Mac mini `jiehandeMini`, port 18765.
- Base: `/Users/jiehan/models/Qwen3-4B-mlx-4bit-phase3-wrapper`.
- Adapter: `/Users/jiehan/models/phase99-multiturn-candidate/adapters.safetensors`, SHA-256 `bfb6901a7aef2c4e5c3b9166a3f0bd982ca7b6ee461ea3e81a6f9a42fe05e37c`.
- Phase 99 metadata says 40 iterations on `phase99-multiturn-data`, resuming from Phase 87. Phase 87 itself ran 8 iterations on a seven-row Phase 81 dataset and resumed from Phase 5.
- Phase 5 resumed from Phase 4 checkpoint 150; Phase 4 trained 150 iterations. Phase 4 data had 3,196 train rows. The Phase 99 adapter is therefore not a full-epoch fit of the 19,621-row clean-v2 dataset.
- Historical adapters and configs are preserved; no adapter weights were modified by this audit.

## Exact input integrity audit

Auditor: `training/scripts/phase108_dataset_integrity_audit.py`. It normalizes NFKC text, removes whitespace, case-folds, and compares per-run HMAC fingerprints. It emits paths, file hashes and counts only—not prompts or completions. Four unit tests pass.

### Proposed primary source

Remote path: `/Users/jiehan/datasets/cybersec-clean-v2`

| Split | Rows | Unique user strings | Exact overlap with other clean-v2 splits | File SHA-256 |
|---|---:|---:|---:|---|
| train | 19,621 | 19,617 | 0 | `63526e22f95e170f2d5b31ae610ffb919f8089499a33320d9ef82d2bb259ba57` |
| valid | 1,089 | 1,088 | 0 | `44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365` |
| test | 1,089 | 1,089 | 0 | `ddf38609d85f5105622ed86c694affa793423df2371f6d20d2fe4bf9399b86ee` |

There were zero exact normalized input-string intersections between any clean-v2 split and the audited Phase 3/4/5, Phase 81/92–95, Phase 99 correction, and Phase 99 multiturn datasets. The targeted Phase 107 v0.2 comparison found zero exact user-prompt matches against the selected Phase 92–95/Phase 99 correction JSONL files (684 rows, zero parse errors). Semantic near-duplicates, hidden data sources, and unrecorded historical training exposure remain unproven.

### Historical correction-data problems

- Phase 3 grounded: 1,440/216/280 train/valid/test rows, with 48 exact user-input strings crossing each split pair.
- Phase 4 balanced: 3,196/354/440 rows, no within-dataset exact split overlap; however 496 train inputs, 54 validation inputs and 90 test inputs exactly overlap their corresponding Phase 3 grounded splits, so these are not novel relative to the Phase 3 checkpoint.
- Phase 5 corrective: train, valid and test files are byte-identical (same SHA-256, 12 rows each). Its validation/test metrics are invalid as independent estimates.
- Phase 81: 7/1/1 rows; not sufficient as broad training data.
- Phase 94 balanced repair: 214/28/28 rows but only 40/19/23 unique user strings; exact cross-split overlap counts train-valid=16, train-test=19, valid-test=12. Its train inputs all overlap Phase 99 multiturn training.
- Phase 95 balanced format: 310/40/40 rows but only 42/21/25 unique strings; exact cross-split overlaps=18/21/14. Its train/valid/test prompt strings match the corresponding Phase 99 multiturn splits (42/21/25); it adds no new user-input coverage to the production adapter's training history.
- Phase 99 multiturn: 316/40/40 rows, only 54/21/25 unique user strings, with cross-split overlaps=18/21/14.
- Phase 99 correction: 8/2/2 unique rows and no exact cross-split overlap, but is too small to provide broad capability improvement by itself.

These findings explain why the small follow-on runs are not a sound next step. Phase 94/95 training logs also show held-out PPL values of 66.796 and 74.147 respectively; these dataset-specific losses are not benchmark quality scores.

## Tokenization and format check for clean-v2

The local Phase 3 wrapper tokenizer parsed every clean-v2 row (zero malformed records). Token counts use the same `user` → `assistant` chat-template rendering and prompt-mask boundary as the installed MLX-LM completion dataset loader. Median formatted total length is 739/735/733 tokens for train/valid/test; p90 is 982/979/980. Four of 19,621 train rows exceed a 2,048-token cap (maximum 2,220); none of the valid/test rows do. A 2,304-token cap retains every row. No content was copied into this report.

## Next gated experiment

1. Snapshot the exact production adapter into a new candidate directory; do not point training output at production.
2. Use only clean-v2 `train.jsonl` for training, preserve its `valid.jsonl` for checkpoint selection and `test.jsonl` for a one-time final LM-loss check. Keep all Phase 107 prompts, answers and outputs out of the training files.
3. Before launching full training, validate MLX-to-HF adapter equivalence on the school A100 path or use a safe Mac mini route that does not stop/modify the production API. The cluster has a BF16 dequantized base and `cyber-cuda` PyTorch environment (PyTorch 2.9.0+cu128, Transformers 5.17.0, safetensors 0.8.0); PEFT is absent, and adapter conversion and end-to-end output parity are not yet verified.
4. Train a candidate with fixed seed, full data lineage, checkpoint/rollback, and completion-only loss masking. Evaluate the candidate on the frozen Phase 107 suite as a repeated validation (reviewers have already seen that suite); create a fresh blind set before any promotion decision.
5. No production adapter/API, rubric or tool permission changes are authorized by this preflight.

## Runtime follow-up — 2026-09-20 15:25 HKT

- The three clean-v2 splits were copied directly from the Mac mini to the Slurm account over an SSH stream; no raw data copy was made in this Git worktree. Cluster destination: `/data3/ieug25/zj225/cyber-model-migration/data/phase108-clean-v2`, directory mode `0700`, JSONL files mode `0600`. All three cluster SHA-256 values exactly match the source hashes above.
- Added a read-only CUDA smoke script, `training/scripts/phase108_hf_adapter_smoke.py`, which checks the 28-projection / 56-tensor MLX-LoRA mapping, loads the Transformers base, and generates a short answer both without and with the active adapter. CPU unit tests verify the matrix orientation and scale formula against the MLX expression; all six Phase108 script unit tests pass.
- The first GPU attempt on the idle Titan X loaded all 398 base shards but failed at generation because that device is compute capability 5.2 and the installed PyTorch build supports SM 7.0+. It does not establish model/adapter compatibility. The script now rejects unsupported devices before loading.
- A second read-only smoke test completed successfully on an RTX 2080 Ti (SM 7.5) using FP16 and a 6 GiB GPU-memory cap with CPU offload. It loaded the Transformers base, attached all 28 projections / 56 tensors from the Phase91 adapter using the MLX matrix orientation and scale, and generated nonempty deterministic outputs with and without the adapter. Slurm job `43844` completed in 2:32 with exit `0`; peak CUDA allocated memory was 5.862 GiB. This verifies that the representation and smoke path work on a supported CUDA device, but not BF16/A100 performance or train throughput.
- The A100 BF16 smoke job `43841` was cancelled after the Mac mini MLX training pilot proved this local path works; it had not started and used no compute. No other Slurm jobs were changed.
- The Mac mini has a local MLX training path (`mlx 0.32.0`, `mlx-lm 0.31.3`) and already contains the exact source data. A 10-iteration isolated pilot completed on 2026-09-20 with 5,755 tokens, train loss 1.583 at the end, four-batch validation loss 2.000 before updates / 1.596 at step 5 / 2.090 at step 10, and peak MLX memory 3.765 GB. This tiny, noisy pilot validates the runtime only; it is not evidence of quality improvement.
- During the pilot the production API stayed listening on port 18765 under the same PID; the production adapter SHA remained `bfb6901a7aef2c4e5c3b9166a3f0bd982ca7b6ee461ea3e81a6f9a42fe05e37c`. System memory pressure remained 46–55% free while training and returned to 73% free afterward. Pilot outputs are isolated at `/Users/jiehan/models/phase108-mini-pilot-20260920` and will not be deployed.
- Because the Mac mini pilot proved this path fits while the production API remains up, the full candidate is configured to train locally rather than waiting for A100 scheduling. The A100 smoke-only job `43841` was cancelled (it was owned by `zj225` and had not started).
- Production API and Phase91 adapter remain unchanged. The full candidate uses a separate output path, one pass over all 19,621 train rows, fixed validation samples during training and the reserved full test split once at the end.

## Full candidate training started — 2026-09-20 15:40 HKT

- Mac mini process PID `43774` is the authoritative Phase108 training process. It loaded the exact Phase91 adapter, reports 1.835M trainable LoRA parameters, and is configured for 19,621 iterations (one shuffled pass, batch 1, gradient accumulation 2) with output `/Users/jiehan/models/phase108-cleanv2-epoch1-20260920`.
- Initial pre-update validation loss on the fixed 32-batch sample: `1.869` (MLX loss; not a benchmark quality score). At 2026-09-20 15:42 HKT it had completed this baseline evaluation and entered training. No checkpoint has yet been reached.
- Memory pressure was 47% free after baseline validation; production API PID `17247` remained listening on port 18765. The live Phase91 adapter SHA is still unchanged.
- Based on the 10-step pilot rate, rough runtime is approximately 21–24 hours including periodic 32-batch validation and one full held-out test-loss pass. This estimate will be recalculated from the first 100-step throughput report. Training may finish without achieving the desired capability; only blind capability evaluation can establish that.
