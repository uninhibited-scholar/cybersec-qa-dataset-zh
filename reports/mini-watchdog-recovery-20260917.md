# Mac mini watchdog panic and recovery

Date: 2026-09-17

## Evidence

- Panic reason: `watchdog timeout: no checkins from watchdogd in 91 seconds`.
- The panic log reported 42 swapfiles and compressor segments at 100%.
- The system had sustained high `kernel_task` CPU usage, consistent with severe unified-memory pressure.
- The panic occurred in Apple watchdog/interrupt-controller code; no third-party kernel extension appeared in the backtrace.

## Recovery verification

- SSH works through `192.168.31.212` and Tailscale `100.83.34.62`.
- Tailscale daemon, custom cyber daemon, and network extension are running.
- Production API `127.0.0.1:18765/health` returns `status: ok`.
- `iogpu.wired_limit_mb` is `0` after reboot, so the prior aggressive 14GB override is not active.
- Candidate Phase 89 process is not running.

## Safety decision

Do not start Phase 89 or change production adapters until a low-memory canary plan is prepared. Keep the default GPU memory limit, use one model process at a time, and retain SSH/Tailscale health checks before and after any model start.
