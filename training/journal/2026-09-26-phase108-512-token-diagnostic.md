# Phase108 exposed 512-token diagnostic — 2026-09-26

## Purpose and limits

The prior 16-case exposed diagnostic produced only `length` at a 128-token cap
for the scale-zero control, parent at scale 5, and corrected-r2 at scale 5.
That cap made response completion indistinguishable from runaway generation.
This follow-up uses the exact same already-exposed 16-case sample and runtime,
with a 512-token cap. It records only response hashes, character counts,
finish reasons, and timings; raw prompts and responses remain on the cluster.
It is a diagnostic only, not a blind score, capability result, inference-scale
selection, or promotion gate.

## Pinned inputs and reproducibility

- Final Slurm script SHA-256:
  `ef2a8a6f9981a59e6144ac82660232a7ea07d98d44a18664c6aa1c507c54a0b9`.
- Replay client SHA-256:
  `f503bc795cb7ad3dee3d88bf09f7527aec06261ce43a1fb8c966a7f66c59b6f1`.
- Loopback sandbox API SHA-256:
  `df1484bd0b01ee72e3b41dbb2a7ceda7b384d1e08f99239ffde68357338f83f7`.
- Exposed sample SHA-256:
  `9a4d398893034b922cc67582089642c553733c856ab2812088b398a2546fbb6b`.
- Parent adapter SHA-256:
  `3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`.
- Corrected-r2 final adapter SHA-256:
  `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`.
- Base config/index SHA-256 values are pinned in the script. Base weight shard
  hashes, previously measured inside a compute allocation, are
  `25094f7fbaef4769da447cb6ebf4a39d99ccc5043856cce1b4f8fc2f91ed9115` and
  `a2fd70328fc4fb518bb40ac806e8c05f21ad12e228648684775f67c28104815d`; the
  script verifies both from inside its Slurm allocation before model loading.
  Do not hash the multi-GB shards on the login node. Each output directory is
  unique and mode 0700; result files are mode 0600. No production endpoint or
  model weights are written.
- Existing corrected-r2 fixed-validation sweep `44617` remains untouched and
  queued; the diagnostic requests only an idle TITANX allocation.

## Local verification and dispatch status

- `bash -n training/slurm/phase108_exposed_scale5_512_diagnostic.sbatch` —
  passed.
- `python3 -m unittest training.scripts.test_phase108_greedy_exposed_replay
  -v` — 3 tests passed.
- `git diff --check` — passed after the final script edit.
- Remote pinned server, replay client, sample, and adapter hashes were checked
  at the controller before job submission; all matched the values above.
- Job `44624` was submitted only after the idle Titan V node and the disk quota
  (280G / 479G, 58.5%) were checked. It started on `titanv1` at 22:50:48 HKT
  with a two-hour limit. The remote copy of the script has the exact SHA above;
  `bash -n` and the remote sample-hash preflight passed. At 22:52 HKT it had
  loaded the base and started its first arm; no aggregate output was complete
  yet. Slurm log path:
  `logs/phase108-scale5-512diag-44624.log`; unique output directory:
  `results/phase108-exposed-scale5-512diag-44624/`.
- A manual attempt to hash base shards on the login node was stopped as soon
  as the running process was noticed. Its PID was confirmed gone. The job
  itself reuses the previously recorded compute-allocation hashes and performs
  those checks inside its scheduled allocation, before model loading.
- Record terminal Slurm state, elapsed time, output hashes, and aggregate
  result after completion. If the runtime exceeds its two-hour cap, preserve
  partial logs and report it as a diagnostic failure, not a model result.

## Interpretation rule

Even if outputs stop before 512 tokens, this exposed sample cannot select a
scale or establish capability. If they still hit the cap, further response
quality comparisons require a properly bounded generation protocol and the
independent replacement blind suite. Continue to use frozen validation only
for loss/checkpoint selection; keep the candidate isolated until all required
data-integrity, capability, format, hallucination, permissions, blind, and
human-review gates pass.
