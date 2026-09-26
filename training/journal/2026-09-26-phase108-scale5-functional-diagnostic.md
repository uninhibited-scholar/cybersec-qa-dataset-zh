# Phase108 exposed-sample full-length scale diagnostic — 2026-09-26

## Motivation

Existing metadata-only diagnostics showed a strong scale association on the
already-exposed 16-row v0.9 sample: both the parent and corrected-r2 adapters
had no first-token EOS at scales 0, 2.5, and 5, but all 16 immediately stopped
at scale 20. The earlier reduced-scale run generated only 16 tokens, so it
could not distinguish a normal completion from hitting the token cap. This
follow-up measures finish reason and output length at a 128-token cap without
storing response text.

## Protocol and isolation

- Reuses only the same exposed 16-case sample from the pinned v0.9 file
  (SHA-256 `9a4d398893034b922cc67582089642c553733c856ab2812088b398a2546fbb6b`);
  it is explicitly not blind, not scored, and not eligible for model
  selection/promotion.
- Runs three matched arms: a scale-zero control using the pinned parent
  adapter, the parent at scale 5, and corrected-r2 at scale 5. The two adapter
  hashes are pinned in the job script.
- Temperature is zero, token cap 128, and tools are empty. The loopback-only
  sandbox refuses tool requests. Result files include only case IDs, response
  hashes, lengths, finish reason, and runtime metadata; server request logs
  suppress payloads. Files are permission-restricted.
- Uses an idle TITANX allocation, separate from the queued A100 fixed
  validation and general Qwen serving job. No production service, weights,
  benchmark, or permissions change.

## Reproducibility and status

- Client SHA-256: `d6d89c18139a8eac0077c9a1c4c38114c4b2d3d3592ffd283c34b56bd45b497d`.
- Slurm script SHA-256: `a486406b995dffc958f76725b2197432bbfa1b7a3800dec79799f0780c9ff398`.
- Focused unit tests: 3 passed. Python bytecode compilation and `bash -n`
  passed. Remote input ID selection was checked against the exact pinned suite
  hash before dispatch.
- Job has not yet been submitted as of this entry. After commit and exact
  remote hash verification, submit once; record its authoritative Slurm ID,
  elapsed time, and aggregate result here. Do not adjust adapter scale or
  claim specialist capability from this diagnostic.

## Interpretation boundary

This can establish whether the immediate-empty symptom persists at scale 5
under a longer cap and the same runtime. It cannot establish response quality,
the correct serving scale, generalization, or promotion eligibility. The
frozen validation and a fresh, independent blind suite remain required.
