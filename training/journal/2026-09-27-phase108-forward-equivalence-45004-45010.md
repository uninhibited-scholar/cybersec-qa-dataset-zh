# Phase108 forward-equivalence diagnostics — 2026-09-27

## Scope

Three isolated CUDA jobs checked whether the custom MLX-layout adapter wrapper
was introducing the exposed immediate-EOS behavior. These jobs did not run
generation, write raw prompts/responses, read blind data or answer keys, or
change production, adapters, permissions, evaluation criteria, or candidate
weights. The exposed-case run used only already-exposed rejected v0.9 case
`p108v9-evidence_boundary-009` (source SHA-256
`9a4d398893034b922cc67582089642c553733c856ab2812088b398a2546fbb6b`). It is
diagnostic metadata, not a blind score or capability result.

## Job outcomes

| Job | Slurm result | Runtime | Finding |
| --- | --- | ---: | --- |
| 45004 | `FAILED 1:0` | 0 s | Infrastructure/preflight attempt stopped before inference; empty log SHA-256 is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Follow-up identified missing synced helper files. |
| 45005 | `COMPLETED 0:0` on `titanv1` | 1m50s | Neutral synthetic input: manual wrapper vs PEFT logits cosine `0.99999499`, max absolute difference `0.015625`, mean absolute difference `0.00286210`, same argmax. EOS ranks were 6013 (base), 2948 (manual scale 20), 2944 (PEFT scale 20); EOS was not top-ranked. Scale 1 also did not put EOS first. |
| 45010 | `COMPLETED 0:0` on `titanv1` | 58s | On the one already-exposed EOS-trigger case, manual vs PEFT scale-20 logits cosine `0.99999750`, max difference `0.03125`, mean difference `0.00587219`, same argmax. Base EOS rank 1613; candidate at scale 20 ranked EOS first (margin 0.578125); candidate at scale 1 ranked EOS 1344 and retained the base top token. |

Job 45005 aggregate log SHA-256:
`75f0aa8fbac805e2fbdfaeaa534eb4f0f820a6a60654957e03e6abfd97c547e1`.
Job 45010 aggregate log SHA-256:
`376ee4fd108b691219fcc20bf2451056e602505ce1d8afe4ec0037442de9d869`.
The 45010 probe SHA-256 was
`a0e84676e2d1706c76e702e0d8d4cd0f829d8973208d136eaa02a5af72a0005f`; its
SBATCH wrapper SHA-256 was
`dcc81631b4fee74d0ec42a718e75fb8e2cf945d03599649a4b6dd1e32faa8fd6`.
The wrapper pinned the adapter SHA-256
`4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`, base
config and shard hashes, exposed fixture hash, loader/test hashes, and ran
four adapter-loader unit tests before the forward comparison.

## Interpretation and next step

The custom inference wrapper agrees numerically with the PEFT validation path
on both the neutral input and the exposed failure input. On the latter, the
scale-20 adapter delta itself raises EOS to the top logit; scale 1 removes
that specific EOS spike. This localizes one reproducible failure to the
adapter-scale interaction rather than a wrapper mismatch. It does **not** show
that scale 1 improves answers, general capability, or safety, and it must not
be used to change a production scale or unseal the prior blind run.

Next, run a separately isolated same-checkpoint loss sensitivity sweep using
only the hash-pinned `valid.jsonl` at scales 1, 2.5, 5, 10, and 20. Treat the
result as checkpoint/scale diagnostic only. A new blind protocol would need
to be frozen before collecting any new blind responses; existing blind
artifacts and the alias map remain sealed.
