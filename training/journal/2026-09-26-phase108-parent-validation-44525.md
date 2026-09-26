# Phase108 parent-adapter fixed validation — 2026-09-26

## Run identity and terminal status

- Slurm job `44525`, `p108-parent-val20`, partition `GPU-MEDIUM`.
- Authoritative `sacct`: `COMPLETED`, exit `0:0`, elapsed `00:03:39`,
  2026-09-26 00:43:50–00:47:29 HKT.
- Remote aggregate output:
  `/data3/ieug25/zj225/cyber-model-migration/results/phase108-parent-fixed-scale-validation-44525.jsonl`.
- Local copy: `training/journal/phase108-fixed-validation-44525.jsonl`.
- Aggregate output SHA-256:
  `a68e6b69f224ac51c0200ecd37bab9fa28b89dd781002d4250753dbc30423a5c`.

## Verified provenance

- Parent adapter SHA-256:
  `3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036`.
- Frozen validation SHA-256:
  `44f46f44b6a3653d0acd799d24b4c6d331a13030eaa4f3e6849a84141b18a365`.
- Validation rows: `1089`; train/test splits read: `false` / `false`.
- Base config SHA-256:
  `260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650`.
- Base safetensors index SHA-256:
  `5e699a61da09415f33a625885364d3889a80acb6ab88aedaf6e195b2612addf4`.
- Validation runner SHA-256:
  `1f3ede835ac356ca8dea9452aca5fecb21deb430de705f7d1d3afd71c1939414`.
- LoRA scale utility SHA-256:
  `966d35d28d3222950c8b1b955838ce36d87f85e9449b53281455381dac4d5849`.
- Job script SHA-256:
  `a5a6674f50023788decdda9e14fa45fb7b49ff318fbece0af68fce988184a7f1`.
- Rank `8`, MLX scale `20`, PEFT alpha `160`, effective scale `20`, maximum
  sequence length `2304`.

## Result and interpretation

- Frozen validation loss: `1.7362299831336085`.
- The output contains only aggregate metadata and was copied to Git after
  verifying all pinned provenance fields and the output hash.
- This is the parent-adapter selection baseline for the pending final-candidate
  fixed-validation comparison in job `44593`. Loss alone is not user-visible
  capability evidence and does not establish suitability for deployment.
- No production API/adapter, evaluation rubric/protocol, or tool permissions
  were changed.
