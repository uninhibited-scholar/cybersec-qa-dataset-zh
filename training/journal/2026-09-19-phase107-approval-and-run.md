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

Update after server startup, collection completion/failure, and reviewer calibration. Raw cases, answer keys, credentials, and raw outputs remain outside Git.
