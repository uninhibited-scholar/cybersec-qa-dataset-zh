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
- Parent adapter: `3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`.
- Corrected-r2 final adapter: `4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`.
- Candidate trained for 7,621 steps from the parent adapter; frozen validation
  on 1,089 rows reported loss 1.7062584871 vs parent 1.7362299831. This is
  loss/checkpoint-selection evidence only, not a user-visible capability claim.
- Candidate manifest SHA `e60ae88a3f491ed94b13f9e26ef0892e5986c838f69dff2fcbf8714185a29636`
  records 19,621 train rows, 7,621 steps, LR `5e-6`, rank 8, MLX scale 20,
  PEFT alpha/effective scale 160/20, and `test_split_read=false`.
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
- Cluster copies matched local hashes: collector
  `8ce85906bd41c097ca9c8a2296bdb73f43ee2a468640a54be1506a66c5788c6e`, tests
  `f3003eaf0d64e0d7a33f4b57407af150acfa839e0c00eaba79598a22924d7161`, SLURM
  wrapper `45f45edd874d5c8b7fdbb27acf13787a26063a8f0fbc01e1e596d5dcc438c0ca`,
  and adapter loader `00ef5d3b1aaada8285b711a68f47c9e00a4fb9dbbd993e8eaf8eefd7426fa371`.
- Cluster-side `bash -n`, `py_compile`, and the three collector unit tests
  passed before scheduling; the tests exercised only synthetic tokens/tensors.

## Dispatch and results

The first three submissions (`44796`–`44798`) terminated during wrapper
preflight; no inference or result directory was created. The first two logs
were insufficiently diagnostic; job `44798` surfaced the incorrect local
parent-SHA pin described below. After correcting the pin, rerun the cluster
unit tests and hash checks, then submit under a new job ID. No model-quality
result exists yet.

Correction verified; the exact pinned inputs and three synthetic-token unit
tests passed on the cluster. SLURM job `44799` started on `titanv1` at
2026-09-27 02:18:40 HKT. All seven content/script hashes passed in the compute
wrapper; its mode-0700 result directory is
`results/phase108-v18r2-blind-44799`. At the latest check it was still
`RUNNING`; no response collection aggregate exists yet.

## Dispatch failures and corrected hash pin

Collection jobs `44796` and `44797` both failed before creating a run
directory; neither performed inference. The second attempt emitted only its
wrapper-start marker. Job `44798` then made the preflight error explicit: I
had transcribed the expected parent SHA incorrectly in the new collector and
SLURM wrapper. This was a local pin error, not a mismatch in the training
input or candidate artifact. The authoritative Phase108 training-start log
(`phase108-scale20-44306.log`, SHA-256
`12e3001df6c0b048f7c1e9af6b303da22c8feea81b7a2b4d2cf16dd1dfb950b9`) records
input path `phase108-step12000-20260920/0012000_adapters.safetensors` and SHA
`3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`. The
current source file, the candidate manifest's `input_mlx_adapter_sha256`, and
the training-start log all agree on that exact hash; its mtime precedes job
44306. The candidate's final adapter SHA and manifest remain unchanged. The
collector/wrapper pin is corrected to the verified value; the failed jobs
remain in SLURM accounting and their unique result directories are absent.

The historical candidate manifest does not include a training-script hash,
so it is not fully reproducible from that manifest alone. The run-start log
and source file do verify the source path/hash; the provenance gap is retained
as a limitation rather than silently repaired retroactively.
