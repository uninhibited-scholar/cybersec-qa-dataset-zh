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
- The initial submission (`44608`) failed closed in one second before model
  loading. Its pinned server hash was `df1484bd...`, while the existing remote
  generic server had changed to `fbae10cc...` and now requires BF16/CUDA. Slurm
  accounting shows no GPU in `AllocTRES`; the output log was empty. This was a
  server-provenance preflight mismatch, not an inference result. The retry uses
  a distinct remote filename for the exact locally pinned, hardware-aware
  server rather than overwriting the newer shared remote server. After exact
  code/input hash verification, submit one bounded diagnostic job and record
  its authoritative Slurm ID, elapsed time, and aggregate result here. Do not
  adjust adapter scale or claim specialist capability from this diagnostic.

- Submission `44609` loaded the sandbox but failed before sending any requests:
  the expected-ID list in the replay client had two adjacent sample IDs in the
  wrong order. The pinned suite hash was correct, and the selected ID *set*
  matches the earlier exposed sample. No model output or inference result was
  produced. The expected ordering is corrected to match the existing
  44550 metadata; the corrected job was resubmitted as `44610` only after the
  pinned hash-and-ID preflight passed on the compute host.

## Completed result — job 44610

The corrected script passed the remote ID/hash preflight and job `44610`
completed on `titanv1` in 10m44s (`COMPLETED`, exit 0). Its three summary
files independently pin the parent and corrected-r2 adapter hashes, base
config/index hashes, server/client/job-script hashes, and the exposed-suite
hash. The summaries were hash-checked before copying; raw response files were
not transferred.

All 16 cases per arm were non-empty at the 128-token cap:

| Arm | Scale | Empty | Non-empty | Finish reason |
|---|---:|---:|---:|---|
| Scale-zero control | 0 | 0/16 | 16/16 | length 16/16 |
| Parent adapter | 5 | 0/16 | 16/16 | length 16/16 |
| Corrected-r2 adapter | 5 | 0/16 | 16/16 | length 16/16 |

Every arm hit the 128-token limit on every case. This confirms only that scale
5 avoided immediate EOS within the cap on this already-exposed sample; it does
not show complete answers or their correctness. Since even the base control
hit the cap, the short run cannot distinguish normal long responses from
runaway/repetitive output. No inference scale was selected and no model was
promoted.

Aggregate summary SHA-256 values:

- base control: `76d9a7bf25e24a7a201c11a0c9ec0f2637bf6a08096aeb5a0d79a9e2a53e88ff`
- parent scale 5: `342341bc64e0f83699631e702c19f28317d714f513109112dbd3481f6dce014e`
- corrected-r2 scale 5: `565a17aa26a0a6e419cc791e026c2b6d82e836f151955d5cd2c736894086cffd`

The three JSON summaries in `phase108-exposed-scale5-44610/` contain aggregate
metadata only and match their cluster SHA-256 values. The next behavior test
must use an appropriately longer generation cap and, before any capability
claim, the replacement independent blind suite; exposed v0.9 remains
disqualified. A100 validation job `44593` and separate Qwen14B service job
`44601` remain independent and queued.

## Interpretation boundary

This can establish whether the immediate-empty symptom persists at scale 5
under a longer cap and the same runtime. It cannot establish response quality,
the correct serving scale, generalization, or promotion eligibility. The
frozen validation and a fresh, independent blind suite remain required.
