# Phase108 v0.8 suite independence audit — 2026-09-26

## Decision

Do not freeze or use v0.8 as a 320-independent-scenario blind holdout. It may
serve as a stratified task-type exercise, but its 320 rows are not 320
independent underlying scenarios. No model inference, candidate selection,
capability score, or deployment decision is based on this audit.

## Private artifact identities

The prompt/source/key files remain local and out of Git. The audit records only
hashes and aggregate findings:

| Artifact | SHA-256 |
|---|---|
| source fixtures | `f83b93af40c3f489b5b8b5e420daed37b1c89d2cca3b5bcbded4d1a6e2c8b9fa` |
| 320-case manifest | `35646c9b4507df0a08db713b8ee3d3a69a45f5f64cef03012e8f2630e1afa5e9` |
| answer keys | `57f5deef3a39bcd3ab0b82b319a1be0773616c646a9a69bda2a5fe9166f50e6a` |
| structural preflight | `ec94f44306fefa8b14eed84150edba1f33d68eae64d96f6a94919b5a56c4e6a2` |
| lexical near-duplicate audit | `e3d82edb50604bf73d5a04b5a2d474325586fdc7de4eed6e779666bdf09b0ae2` |

The structural preflight reports 320 cases, 40 per required category, and 320
unique identifiers/family labels. Those labels did not establish semantic
independence.

## Independent semantic review

Two reviewers who did not author the fixtures inspected the source/cases and
near-duplicate flags without seeing model outputs, scores, or identities. Both
found that the same 40 core incident motifs recur once in each of the eight
categories. The task requested changes, but the underlying incident is shared;
therefore the suite represents 40 scenario motifs crossed with eight task
types, not 320 independent scenarios. Under a strict unique-scenario
requirement, 280 cases need replacement or materially distinct source
scenarios.

Both reviewers also flagged:

- `p108v8-threat_modeling-028` / `p108v8-multiturn-003`: shared core incident;
  the latter adds a second-turn fact but does not remove the shared scenario.
- `p108v8-multiturn-013` / `p108v8-multiturn-028`: same two incident motifs
  composed in reverse order; revise one.

Their review supports task-type diversity, not scenario-level independence,
pretraining cleanliness, or deployment readiness.

## Exact-overlap scan against cluster corpora

The v0.8 user-message strings were fingerprinted locally with a one-run random
HMAC key; only keyed hashes were sent over SSH to compare with cluster data.
Neither the key, fingerprints, nor prompt text were persisted. The scan
covered 400 distinct user-message strings across the following 16 available
train/valid/test files; there were zero exact normalized user-text overlaps and
zero parse errors:

| Cluster corpus | Split rows | File SHA-256 (train / valid / test where present) |
|---|---:|---|
| `phase108-clean-v2` | 19,621 / 1,089 / 1,089 | `63526e22f95e170f2d5b31ae610ffb919f8089499a33320d9ef82d2bb259ba57` / `44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365` / `ddf38609d85f5105622ed86c694affa793423df2371f6d20d2fe4bf9399b86ee` |
| `phase108-clean-v3-formatmix` | 19,621 / 1,089 | `2cfc505dcf47af52bd8b4abdd1e5eb597f8858564e28e3c77f9678d303344c5d` / `aba88e9e2a2895084896bb495d99f6c78eb560de5f06c66b526c2f911f121881` |
| `phase108-clean-v4-bare` | 19,621 / 1,089 | `e2aa9be1d31c5392d2c6f15398371971bf54590c20440967e73cfa2e4afec130` / `473f5b39cc1ba6e37dc51c38859a516bae167b80cc8bb56dc7237c9ec85660cd` |
| `phase99-correction-data` | 8 / 2 / 2 | `33da81f4f666feebe240ec54b4d6734dd03038c8dbfaf1c630b9240bdb448428` / `dc0079931c76c9535dabe4686dcf8f9e56e7fedc35c170ca8161faa78af898f4` / `98474bf846be96d594578e52de9803d01bf48e3288c761e7e62b389ca759d663` |
| `phase99-format-status-data` | 10 / 2 / 2 | `c270b7a801120b7128c5fb4b4c7cebb897aab0e9a16139488898f4190c1dff06` / `3beb51f11e71509ded7748d9cb4dc8f9ffd64e76f469665b5d0e06c6830a85f0` / `3beb51f11e71509ded7748d9cb4dc8f9ffd64e76f469665b5d0e06c6830a85f0` |
| `phase99-multiturn-data` | 316 / 40 / 40 | `fbbae3aea09e2deb4f59794ea78ded71db8fa4ce5ef2c61c54e48182d050c377` / `b4f47c521f5c5e2063b9541febe93ec340a0ad6868f78295f086fea2c91f02d0` / `da98d8c0e020dc9230b8ea95e3c46ea9be71889a063ffdc4692807413801f6bd` |

The exact-overlap scan is narrow: it cannot detect semantic paraphrases,
pretraining contamination, unlisted data copies, or exposure outside the
searched cluster result/log inventory. A filename/content-ID search found no
`p108v8` identifiers in the current cluster `results/` or `logs/`; that is
supporting inventory evidence, not proof that the suite was never exposed.

## Next gate

Build a replacement source with at least 300 materially distinct underlying
scenarios—not category rewrites of a shared motif set—then rerun exact-overlap,
near-duplicate, and independent semantic review. Freeze source/case/key hashes
only after every gate passes. Keep all model outputs, Phase91 production
settings, adapter weights, scoring rubric, inference protocol, and permissions
unchanged until then.
