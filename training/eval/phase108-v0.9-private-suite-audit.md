# Phase108 v0.9 private candidate-suite audit — provisional

**Status (corrected 2026-09-26):** This suite was sampled for a 16-case
Phase108 diagnostic (Slurm job 44430), so it is no longer an untouched holdout.
It remains unfrozen, has unresolved semantic-review requirements, and is not a
valid fresh blind promotion set. Do not use it for checkpoint selection,
capability scoring, or deployment gates.

## Private artifacts

- source fixture SHA-256:
  `bdf25db35d1fb7a060435c3c1681b36d7e8cd3eb252d41d86fc2a28d54c2f298`
- prompt manifest SHA-256:
  `9a4d398893034b922cc67582089642c553733c856ab2812088b398a2546fbb6b`
- answer-key SHA-256:
  `7135c8c3c3594046f4f952ea4a2a4e01a52f19e78d509798d732f17ae5bd7427`

The artifacts are permission-restricted and gitignored. This file deliberately
contains neither prompt text nor answer-key text.

## Completed automated checks

- 320 cases, exactly 40 in each of the eight required strata;
- 320 distinct normalized prompts and fixture IDs;
- 40 structured user/assistant/user multi-turn cases with distinct user-turn
  sequences;
- source structural-diversity preflight passed (40 labeled scenario families,
  8 artifact kinds, and 40 decision foci in every stratum);
- manifest/key structural validator passed for `phase108-v0.9`; and
- exact normalized-overlap scan passed with zero overlaps against 179 local
  train/validation/test/batch/historical JSONL files (43,714 indexed prompts,
  zero unrecognized rows).

## Near-duplicate triage

The user-message lexical audit at 0.52 reported two flagged pairs, both
involving multi-turn material; the maximum within-stratum similarity was
0.5202. This is a reviewer queue, not a failure being silently waived. The
earlier v0.3 generated draft had 5,350 flags and remains rejected.

## Required next gate

A reviewer independent of fixture authorship must examine the two flagged
pairs and perform the semantic scenario-family audit across all strata. The
review must decide whether each case has a materially distinct underlying
system, artifact, or decision. Only after a pass is documented may the source
and derived manifest/key hashes be frozen and sealed for a new four-arm blind
collection. No Phase91 endpoint, candidate adapter, inference protocol, rubric,
or tool permission has changed.

## Exposure correction

- Contrary to the original provisional status above, job `44430` read the
  suite and selected 16 cases using Python `random.Random(20260925).sample`.
  Its output retained only case IDs, response SHA-256 values, and character
  counts; it reported 16/16 empty outputs from the then-tested step-7000
  checkpoint. The result JSONL SHA-256 is
  `6f70e9192b019bc87ba834b903fd4f0aa972a067db1996bd080897600b8a36c6`.
- A later paired diagnostic on four public probes showed non-empty responses
  from both the exact parent and corrected-r2 final adapter; it did not use
  v0.9. Therefore the 16/16 result is unresolved and must not be generalized
  to the final candidate. A same-16 replay is diagnostic-only and must retain
  outputs outside Git; it cannot restore blind status.
- Any promotion evaluation requires a distinct fresh suite with new source
  material, overlap/semantic-diversity review, frozen hashes, and an
  independently held identity map.
