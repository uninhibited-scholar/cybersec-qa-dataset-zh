# Phase 107 — collect Phase 91 arm while reference GPUs queue

## Why

The approved A100 reference job `43695` is still pending for resources. Rather than leaving the entire benchmark idle, collect the already-approved Phase 91 production arm first, then let the existing full collector resume the two references into the same blinded artifact directory when they become available.

## Invariants

- Phase 107 v0.2 cases, answer keys, rubric v0.1, inference protocol v0.1, and approved prompt corrigendum v0.1.1 are unchanged.
- Phase 91 production API, base, adapter, and tool permissions are unchanged.
- The partial run uses the same case order seed, per-case randomized arm order, sealed alias map, generation settings, parser, and append-only response file as the eventual three-arm run.
- Answer keys are not loaded. Raw responses and sealed identity mapping remain outside Git in `/tmp/phase107-v0.2.A4Jnn2` (directory mode 0700; private files mode 0600).

## Implementation and validation

- Extended `phase107_collect_blind.py` with a `--systems` selector so approved arms can be collected in stages and resumed from existing `(case_id, alias)` rows. Default remains all three systems.
- The eventual full run reads the same `sealed-identities.json` and `blind-responses.jsonl`, skips already collected Phase 91 rows, and collects only the two references.
- `python3 -m py_compile training/eval/phase107_collect_blind.py` passed.
- `python3 -m pytest -q training/eval`: 19 passed after adding the partial-resume count test.
- `git diff --check` passed.

## Runtime state at start

- Phase 91 API health and authorized `/v1/models` preflight passed through the Mac mini SSH tunnel.
- Using the Mac mini's available CPU/memory headroom, the Phase 91-only collector completed all 320 cases at approximately 21:13 HKT on 2026-09-19.
- Post-run metadata audit: 320 rows, 320 unique case IDs, one blinded alias, all 320 classified `ok` (transport/completion status only, not a quality score).
- Private output directory remains mode 0700 and response file mode 0600. Sealed identity mapping and raw answer content were not opened for scoring before all arms are available.
- Phase 91 API health remained OK after collection; production model/adapter and service configuration were not changed.
- A100 job `43695` remains pending; the separate FPNet job `43670` is unrelated and untouched.

## Limits

This is collection of the production endpoint arm, not an ability score. `ok` only means the request produced a response under the collector's transport checks. No score, model rank, parity claim, or deployment decision is made until all three blinded arms are complete and the frozen human review gate is satisfied.
