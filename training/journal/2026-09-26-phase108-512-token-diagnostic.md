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

- Slurm script SHA-256:
  `c31e5b1c6202cb91f778724b18398dbe738ce2a3efe8439f9679c83511ca58cf`.
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
- Base config/index SHA-256 values are pinned in the script and checked before
  model loading. Each output directory is unique and mode 0700; result files
  are mode 0600. No production endpoint or model weights are written.
- Existing corrected-r2 fixed-validation sweep `44617` remains untouched and
  queued; the diagnostic requests only an idle TITANX allocation.

## Local verification and dispatch status

- `bash -n training/slurm/phase108_exposed_scale5_512_diagnostic.sbatch` —
  passed.
- `python3 -m unittest training.scripts.test_phase108_greedy_exposed_replay
  -v` — 3 tests passed.
- `git diff --check` — passed.
- Remote pinned server, replay client, sample, and adapter hashes were checked
  at the controller before job submission; all matched the values above.
- At journal creation, this run has not yet been submitted. Record the
  authoritative Slurm ID, state, elapsed time, output hashes, and aggregate
  result only after the job completes. If the runtime exceeds its 2-hour cap,
  preserve partial logs and report it as a diagnostic failure, not a model
  result.

## Interpretation rule

Even if outputs stop before 512 tokens, this exposed sample cannot select a
scale or establish capability. If they still hit the cap, further response
quality comparisons require a properly bounded generation protocol and the
independent replacement blind suite. Continue to use frozen validation only
for loss/checkpoint selection; keep the candidate isolated until all required
data-integrity, capability, format, hallucination, permissions, blind, and
human-review gates pass.
