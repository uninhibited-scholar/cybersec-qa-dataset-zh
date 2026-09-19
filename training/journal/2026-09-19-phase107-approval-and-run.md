# 2026-09-19 — Phase 107 v0.1 approval and blind-run preparation

## Authorization and frozen standards

- User explicitly approved Phase 107 rubric v0.1 and inference protocol v0.1 and directed use of the v0.2 case bank for blind evaluation.
- Frozen copies are `training/eval/phase107-rubric-v0.1.md` and `training/eval/phase107-inference-protocol-v0.1.md`. The earlier `*-draft.md` files remain historical drafts.
- The rubric still requires independent calibration by at least two reviewers on a stratified prompt/key sample and blind critical-failure adjudication before scores, rankings, parity claims, or promotion recommendations are released. This run may collect blind outputs and prepare a reviewer bundle; it must not unseal identities or score before that gate.

## Scope and safety

- Suite: 320 private v0.2 cases, 40 in each of eight strata. Inputs are the authoritative `messages` arrays. The separate answer-key file is not loaded by the collector.
- Use the Phase 91 production endpoint read-only, plus the two local reference model runtimes. No model weights, adapters, API service configuration, tools, network exposure, or deployment state are changed.
- The Mac mini credential is read remotely from its existing user-protected token file over SSH into process memory only. It is never printed, committed, or written to artifacts.
- Reference servers are intended to listen only on compute-node loopback; reverse forwards bind to login-node loopback; workstation access is through SSH forwards. No public or campus-wide API listener is opened.
- User's unrelated Slurm job 43670 remains untouched.

## Runtime availability evidence

- From the workstation, SSH and TCP port 18765 reach `192.168.31.212`; SSH to `jiehan@192.168.31.212` confirmed host `jiehandeMini`, user `jiehan`, and local health response `{"status":"ok","model":"qwen-cyber-local"}`.
- Mini service credential path/configuration were inspected without reading or emitting the credential. The token is not present in LaunchAgent environment variables.
- School cluster login access works as `zj225`. At the availability check, A100-3 was idle with one A100-40G; other GPU nodes were occupied. Existing user job 43670 on TitanX was preserved.
- Reference model files and llama.cpp runtime remain checksum-pinned as documented in `phase107-reference-runtime-status-2026-09-19.md`.

## Run design

- A separate Slurm job starts both reference servers on the one available A100, each on compute-node loopback, with no Web UI. If both cannot coexist in available GPU memory, stop the reference job and record infrastructure failure; do not treat it as model-quality evidence.
- A workstation coordinator will randomize case order and per-case arm order, use global blind aliases, and write each completed response immediately to an external mode-0600 JSONL file. Alias mapping is separately sealed outside Git.
- All arms receive the same ordered case messages; references receive the frozen effective system prompt. Tool inventory is empty. Output ceiling is 700 tokens; temperature 0.12, top-p 0.9, repeat controls are pinned. Phase 91 worker retries/guards/post-processing remain enabled and are disclosed as an endpoint-level asymmetry.
- Phase 91 SSE emits a full completed answer in one content chunk; its first-content latency is not token-level TTFT and must not be compared as such.
- Evaluator-client retries are zero; per-case timeout is 300 seconds. Transport, timeout, parse, empty, and model outcomes are distinct.

## Pending result record

Two independent reviewer agents completed a 16-case stratified calibration without seeing outputs or identities. The calibration record is `training/eval/phase107-reviewer-calibration-2026-09-19.md`; one known key mismatch is excluded from scoring, two multi-turn keys are interpreted only against claims actually present in the transcript, and one prompt-injection case may be dimensionally unscorable. No frozen rubric, prompt, or answer-key bytes were changed.

At 2026-09-19 13:42 HKT, Slurm job `43685` was submitted for the isolated A100 reference servers and remained `PENDING (Resources)` at the latest verified poll. A local durable watcher (`phase107_wait_and_collect.py`, PID 94728 at the latest check) waits for server health, then starts the randomized three-arm collection and releases only job 43685 on completion/failure. At this checkpoint no private case has been sent and no response artifact exists. Raw cases, answer keys, credentials, and raw outputs remain outside Git.

At 2026-09-19 13:52 HKT, the same job `43685` was re-polled and remained `PENDING (Resources)` with a scheduler estimate of 18:02 HKT on `a100-1`; local watcher PID 94728 remained alive. The output directory still contained only `driver.log`, so no prompts had been sent and no model results existed. A read-only resource check found A100-40G nodes in use/mixed or planned, both 20-GB MIG slices on `a100-2` mixed, the RTX 3090 mixed, and other GPU partitions occupied; the idle `test` node has no GPU. No alternative resource was free without displacing another job or changing the approved run setup, so job 43685 was left intact. This is a queue-status checkpoint, not a change to the model capability assessment.

At 2026-09-19 13:54 HKT, scheduler details explain the estimate: `a100-1` has two A100-40G GPUs and its current two-GPU allocation has a 1-day-23-hour limit from 2026-09-17 19:02, ending at 2026-09-19 18:02. Job `43685` is scheduled immediately after that allocation. No attempt was made to preempt, modify, or inspect its workload; the existing Phase 107 reservation and watcher remain unchanged.

At 2026-09-19 13:57 HKT, the exact-overlap scan was rerun using the v0.2 execution manifest and answer-key files (not the superseded v0.1 manifest). It scanned 188 workspace JSONL files and 21,946 normalized training/validation/test strings; all 320 case/key IDs matched, with zero parse errors, unrecognized rows, or exact overlaps. The v0.2 near-duplicate scan also reproduced the same four low-threshold lexical pairs already manually reviewed; it is lexical triage, not semantic-independence certification. Both authoritative hashes match the frozen v0.2 manifest/key hashes in the suite audit. Detailed JSON outputs remain ignored/local; the tracked suite audit records the aggregate and limitations.

At 2026-09-19 13:58 HKT, `phase107_suite_validate.py` passed against the exact v0.2 manifest and key: 320 cases, 40 per stratum, 40 unique structured multi-turn histories, zero structural errors; both hashes matched the frozen values. `test_phase107_builder.py` passed (5 tests). These are dataset-structure checks only; no model response or score exists yet.

At 2026-09-19 14:05 HKT, a read-only AST comparison found the frozen collector's reference `SYSTEM_PROMPT` is not byte-identical to the effective no-tool system content composed by the production Phase 91 worker: collector 426 Unicode characters / SHA-256 `8ece8f47d1fcdca21bdcc8174539ad29182bbaaaf3eb7b303d5536aaaf53ade5`; worker-composed content 425 characters / SHA-256 `6017e9aab198e717f3d61082e08e45ca6fd0afa2158f750c43e1966110efe57e`. Differences are one newline delimiter and two literal backtick characters. Worker source hash remains `a4936301d54bb08bf8b7fa82847e090bbba827c6815513dd5d2d3ae88f7302cb`. Since protocol v0.1 is frozen, no prompt/protocol bytes were changed. To prevent an invalid comparison, the local watcher was sent SIGTERM; its own handler cancelled only owned pending Slurm job `43685` (confirmed `CANCELLED`, never started). Output directory contains only the driver log; no benchmark case was sent and no model result exists. Await user approval before correcting the reference prompt and resubmitting.

At 2026-09-19 14:06 HKT, post-cancellation checks found no local Phase 107 coordinator, collector, llama-server process, or listener on reference-forward ports 18181/18182. Slurm accounting still reports job `43685` as cancelled with zero runtime. The private output directory contains only `driver.log`. The remote Phase 91 health endpoint still reports `qwen-cyber-local`; no production configuration or model was changed.
