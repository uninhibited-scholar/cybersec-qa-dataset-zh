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

## Follow-up resource check

- At 21:16 HKT, the cluster scheduler still showed job `43695` pending for resources with scheduled start `2026-09-21T13:44:13`.
- The general `test` partition had two 1-CPU nodes with aggregate CPU state `0/1/1/2` (one idle CPU, one unavailable); it is not a substantial CPU substitute for the queued A100 reference run. The unrelated `43670` job remains running on `titanx1` and untouched.
- The Mac mini is reachable, reports 16 GiB unified memory, and its Phase 91 health endpoint remains OK. The Phase 91 worker is running but idle after the 320-case collection. No production changes or further training were made.
- CPU capacity is being used for local collection and can support bounded offline work; model changes remain deferred until the blinded comparison identifies an evidence-based gap, avoiding speculative fine-tuning and overfit.
- To test the CPU fallback without touching the private benchmark, added `training/eval/phase107_cpu_reference_probe.sbatch`: one pinned reference GGUF, CPU-only (`n_gpu_layers=0`), 12 CPUs/48 GiB, one neutral `READY` request with a 700-token ceiling, 15-minute wall limit, and summary-only timing/token metadata. It does not start either API or expose a network listener beyond node loopback.
- Probe `43747` was scheduled on `a100-1` and failed before model load/request because that host lacks `GLIBC_2.38` and `GLIBCXX_3.4.32`; this is an infrastructure incompatibility, not model-quality evidence. An earlier backfill estimate pointed the full A100 job `43695` at `a100-1`, but the current scheduler query no longer exposes a predicted node. Its existing readiness gate remains important: no benchmark prompts will be sent unless both reference servers actually load and pass health checks.
- Re-ran the probe pinned to the already runtime-validated `a100-3`. GPT-OSS (`43751`) loaded in about 57 seconds, returned a nonempty response, and generated 58 tokens at 14.10 tokens/s; job completed cleanly. Gemma (`43755`) loaded and generated 64 tokens, but the short cap ended in its reasoning channel with no visible answer; this probe did not pass. After raising the smoke cap to the protocol's 700 tokens, Gemma (`43758`) returned HTTP 200, a nonempty final answer, 114 completion tokens, and stopped normally; load+health took 16 seconds and the request 14 seconds, with measured generation around 8.06 tokens/s. These are operational CPU-only smokes, not Phase 107 cases or quality scores.
- Based on the CPU smokes, prepared `training/eval/phase107_reference_servers_cpu.sbatch` to serve the exact pinned GGUFs on loopback with the same model templates, prompt path, reasoning mode, and sampling settings, using 12 CPUs/48 GiB and no GPU. The collector now records `reference_execution_mode` separately from the frozen content/scoring settings. This is a hardware-backend variation explicitly requested by the user; it will be disclosed and must not be presented as an exact GPU-runtime reproduction.
- First dual-server attempt `43759` loaded both references and passed their local health checks on `a100-3`, but its compute-node-initiated reverse SSH tunnel failed because the compute node had no usable login credential. No benchmark prompts were sent. A workstation-to-compute SSH ProxyJump also failed target-node authentication. Do not weaken host authentication or expose node ports as a workaround.
- Added an isolated `--reference-local` collector mode that requires a complete existing Phase 91 arm, exact frozen suite/protocol hashes, and the original sealed alias map; it bypasses the unavailable mini and tunnel only when running beside loopback reference servers. The Phase 91-only responses, sealed run manifest/map, test cases (no answer keys), and collector were staged in a mode-0700 remote directory for a reference-only continuation. File hashes were checked; each staged file is mode 0600. No model identities or raw response contents were opened.
- A second CPU-only server allocation, `43760`, is running on `a100-3`; both models are loaded, both health checks passed, and APIs bind only to node loopback. The benchmark-reference collector has not yet started; no reference response has yet been collected.
- First compute-local collector invocation failed before the first prompt because the new `--reference-local` branch referenced a JSONL reader not yet present in the collector; added the reader and a test. This was caught in preflight with zero benchmark requests sent.
- Second compute-local invocation validated the staged Phase 91 arm and reference endpoints but still ran the normal authorized `/v1/models` preflight against Phase 91, which is intentionally unavailable from the cluster. It aborted before any benchmark request; the preflight is now skipped only in `--reference-local` mode, which is restricted to a full three-arm resume and still validates the Phase 91 manifest/hash evidence.
- Static shell syntax, collector byte-compilation, `git diff --check`, and all 24 evaluation tests pass. The approved A100 evaluation job `43695` remains unchanged and pending for resources.
- After the two fail-closed fixes, the compute-local collector started under Slurm step `43760.3` at about 21:51 HKT. It reused the exact 320 saved Phase 91 rows and the original alias map, then began the 640 reference requests. At the first progress checkpoint, 3 reference responses were durably appended: 1 `ok`, 1 `truncated` at the fixed 700-token ceiling, and 1 `empty`; no answer content or alias mapping was opened. These classifications are raw output/transport facts, not comparative scores. Collection is ongoing and resumable.

## Limits

This is collection of the production endpoint arm, not an ability score. `ok` only means the request produced a response under the collector's transport checks. No score, model rank, parity claim, or deployment decision is made until all three blinded arms are complete and the frozen human review gate is satisfied.
