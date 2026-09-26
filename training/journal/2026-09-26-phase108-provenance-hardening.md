# Phase108 training provenance hardening — 2026-09-26

## Scope and current cluster state

This change is preparation for a future isolated Phase108 retraining run. It
does not change the production API or adapter, the current candidate weights,
the benchmark/rubric, permissions, or any train/validation/test data.

At 2026-09-26 17:22 HKT, the CUHK scheduler reported the fixed validation job
`44593` (`p108-follow-val`) and Qwen14B service job `44601` as `PENDING`
(`Priority`). The independent public benchmark jobs were active; no Phase108
training process was running. The cluster quota was 280G/479G (58.5%).

The existing corrected-r2 candidate still has a failed exposed functional
replay (16/16 empty outputs on the exposed v0.9 set); it is not eligible for
promotion. The pending fixed-loss evaluation is diagnostic only and cannot
override that functional failure. Historical formatmix and bare-canary
manifests lack exact train/validation file hashes and complete trainer/job
script provenance; because their inputs may have changed since the runs, this
gap cannot be repaired retroactively by hashing the current files.

## Change

`phase108_cuda_resume_train.py` now records SHA-256 fingerprints for:

- the exact train and validation JSONL files (and confirms they did not change
  between fingerprinting and parsing; the test split remains unread);
- the base model config, safetensors index, every indexed weight shard, and
  available tokenizer/chat-template files;
- the source adapter, training runner, scale utility, provenance utility, and
  exact submitted Slurm script;
- Slurm job ID, Git commit when available, Python/package versions, CUDA
  runtime/device, and all relevant training arguments.

The scale-corrected Slurm wrapper now supplies its exact submitted script path.
Missing model shards or a data file that changes while being fingerprinted
fail closed before training.

## Verification

- `python3 -m unittest training.scripts.test_phase108_run_provenance training.scripts.test_phase108_lora_scale -v` — 6 tests passed.
- `python3 -m py_compile` for the updated trainer and provenance utility — passed.
- `bash -n training/slurm/phase108_cuda_scale_corrected.sbatch` — passed.
- `git diff --check` — passed.

No new GPU job was submitted in this step. Before a future training run, the
exact script files must be synchronized to the cluster and their hashes
verified there; do not reuse an older large-partition wrapper until it passes
`--job-script` and carries the same provenance behavior.
