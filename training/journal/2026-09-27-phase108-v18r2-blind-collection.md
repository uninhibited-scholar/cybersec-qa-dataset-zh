# Phase108 v1.8-rev2 blinded raw-weight collection

## Scope and guardrails

This run compares the frozen base, Phase108 parent adapter, and corrected-r2
candidate in one isolated Transformers/CUDA runtime. It is a blinded response
collection only: no automatic score, capability claim, candidate selection,
production deployment, or tool-permission change. It does not change the
Phase107 rubric or inference protocol, the production API/adapter, or any
candidate weights. Answer keys are not copied to the compute node or opened by
the collector. Raw answers and the alias map remain mode-0600 private outputs.

The reviewer-frozen Phase108 v1.8-rev2 suite is pinned by freeze-record SHA
`1dd603084fe3f026954ead8cb55004514b1c5b43a3b3219b0b10b0489ac0d5bf`, cases
SHA `c028b564d2273fc6779f248918511fa2bff0fe73abc4c7bb4ab6051ecc3b91c9`, and
answer-key SHA `f79828a550fb80cd84aba7faa593cd84a4f47e08ee8afc358957726de17a4015`.
The no-tool system prompt was compared byte-for-byte with the frozen Phase107
protocol; its SHA is `8ece8f47d1fcdca21bdcc8174539ad29182bbaaaf3eb7b303d5536aaaf53ade5`.

## Pinned model inputs

- Base config/index SHA: `260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650` /
  `5e699a61da09415f33a625885364d3889a80acb6ab88aedaf6e195b2612addf4`.
- Base weight shard SHA values are embedded in the collector and are verified
  from inside the scheduled compute allocation before model loading.
- Parent adapter: `3ed1a85e7b021e1498332a525bfa4bb75b336a03579d526f8210f1576317036`.
- Corrected-r2 final adapter: `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`.
- Candidate trained for 7,621 steps from the parent adapter; frozen validation
  on 1,089 rows reported loss 1.7062584871 vs parent 1.7362299831. This is
  loss/checkpoint-selection evidence only, not a user-visible capability claim.
- Train-only exact contamination scan: 19,621 training rows, 0 exact overlaps,
  0 parse errors/unrecognized rows; audit SHA
  `f9b9b8d8d3032dae0b6471da54cc86a076fd8c76b4107d5abdcc4ff4a5cf3c44`.
  Validation/test splits were not read by that scan. This is only an exact
  overlap result, not proof against semantic or pretraining contamination.

## Collection protocol

The runner pins all input hashes, uses the protocol's exact no-tool system
instruction, sends each sealed user/assistant message sequence unchanged, and
uses temperature 0.12, top-p 0.9, top-k disabled, a 700-token cap, and a
1.12 repetition penalty over the latest 128 generated tokens. Sampling seeds
are case-derived and shared across arms. Candidate and parent use the
training-declared effective adapter scale 20; no scale sweep or blind-set
parameter selection is performed. Qwen3 thinking text is excluded from the
stored final answer; an unclosed thinking segment is counted as no visible
answer, and tool-control markers are counted separately. Each case is a fresh
conversation. The three arm labels and per-arm case order are randomized.

Runtime/template parity with the Phase91 production endpoint is not claimed:
this is a same-runtime raw-weight comparison using the frozen dequantized base
and its pinned tokenizer template, not an end-to-end Harness comparison. The
collector saves raw final answers, but never prompts or keys, to a private
compute-side directory. Only hash-bound aggregate findings are intended for
Git after the job is verified.

## Pre-dispatch verification

- Collector: `training/scripts/phase108_blind_collection_v18r2.py`.
- SLURM wrapper: `training/slurm/phase108_blind_collection_v18r2.sbatch`.
- Unit tests cover recent-window repetition handling, hiding unclosed
  reasoning, and tool-marker detection; run in the cluster `coevo` environment
  before dispatch.
- Chosen resource: an idle `GPU-TITANX` compute node through SLURM; no model
  inference runs on the login node. Output path is unique per job ID and mode
  0700. The active general Qwen service job is not modified.

## Dispatch and results

Pending pre-dispatch test, synchronized-file hash verification, job ID,
terminal status, result hashes, and alias-blind aggregate findings.
