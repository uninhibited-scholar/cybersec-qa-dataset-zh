# Phase108 v1.0 pilot disposition — 2026-09-26

## Current artifact audit

The local, ignored v1.0 pilot is not a usable independent blind suite:

- It contains 40 cases, all in `evidence_boundary`; the required suite is 320
  cases with 40 in each of eight strata.
- The saved structural preflight fails with 22 errors, including the missing
  seven strata. The evidence-boundary cases meet the preflight's labeled
  structural-diversity counts, but the checker itself warns that this is not a
  semantic-novelty or contamination proof.
- The exact-overlap report says only that no overlap was found in its scanned
  scope and explicitly disclaims clean certification; it reports 10
  unrecognized rows. The near-duplicate report likewise disclaims semantic
  certification.
- Artifact hashes (local private files; no prompt/key content copied here):
  - cases: `d330ae25f5a8e8b8a38ee98f540ab69f3518b32e4c81568216fc5ec10c5496c5`
  - answer keys: `9908d8bd42bca791f9d3c2406e0cedd827acd5c2b4a7863e3078d49aa93ef677`
  - source fixtures: `039a74f6b31015b04e6765d9f94fc24b9ef22d0490ce9ebad74e92b60e96886`

## Disposition

Do not use v1.0 for candidate selection, capability scoring, or promotion. Its
model-exposure history is not established well enough to certify it as an
untouched holdout, and its coverage is incomplete regardless. v0.9 is already
exposed and also ineligible. Build a fresh 320-case suite from independently
authored roots, then run the specified contamination, lexical, structural, and
independent semantic reviews before freezing any manifest or sending prompts.

This audit does not change the rubric, inference protocol, candidate, or
production service. No inference was run.
