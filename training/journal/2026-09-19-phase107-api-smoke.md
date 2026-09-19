# 2026-09-19 — Phase 107 reference chat API smoke

## Work performed

- Added `training/eval/phase107_openai_api_smoke.sbatch`: a bounded Slurm allocation using two RTX 2080 Ti GPUs, a loopback-only `llama-server` (`127.0.0.1`, no Web UI, no tools), and a synthetic short-code multi-turn exchange over `/v1/chat/completions`.
- First run, Slurm job 43678, loaded GPT-OSS 20B and processed the request, but exited 127 because the cluster had `python3` rather than `python`. No response body was printed or retained; no benchmark content was used.
- Fixed the validator to call `python3`. Second run, job 43679, completed in 15 seconds with exit 0; the JSON schema, one-choice completion, stop finish reason, and expected short-code presence in final content passed. The model output itself was not printed.
- The initial cold attempt showed the first model-page-cache load is much slower than the warm rerun. Schedule actual reference inference with realistic cold-start allowance and do not treat smoke latency as steady-state benchmark latency.
- Confirmed via `squeue`/`sacct` that both smoke jobs are terminal; the only remaining visible Slurm job was the user's existing `fpnet_train`, which was not changed. The temporary server exited through the script's cleanup trap.
- A remote unauthenticated GET to Phase 91 `/v1/models` returned HTTP 401. Health over SSH is good. No API token or other credential was read, used, or printed.
- The school cluster login could not connect to the Mac mini Phase 91 API via either `192.168.31.212` or the mini's Tailscale address `100.93.176.125` (3-second connection timeouts). A read-only plist inspection showed only `CYBER_API_HOST` and `CYBER_API_PORT` among relevant LaunchAgent environment key names; no credential value was inspected. The cluster-to-mini path is not available as-is.

## Boundaries

- This used only an artificial non-cyber multi-turn prompt; no Phase 107 case, answer key, score, or training sample was sent.
- No rubric or scoring rule was changed. No Phase 91 service, model, adapter, or tool permission was modified.
- The Phase 91 evaluation arm will require an already authorized bearer credential supplied without logging; this note does not authorize extracting secrets from the mini's launchd environment.
- Do not broaden API binding, add a public tunnel, or open firewall access. If approved, execute the reference arms on the cluster and the Phase 91 arm from a network-reachable user device, then exchange blinded outputs via existing SSH/SCP.
