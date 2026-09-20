#!/usr/bin/env python3
"""Wait for the approved Slurm reference allocation, collect blind outputs, release it."""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def run(command: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout)


def accounting_state(output: str) -> str:
    """Return the first Slurm accounting state, or unknown when unavailable."""
    for line in output.splitlines():
        fields = line.split()
        if fields:
            return fields[0].split("+")[0]
    return "unknown"


def is_terminal_state(state: str) -> bool:
    return state not in {"", "unknown", "PENDING", "CONFIGURING", "RUNNING", "COMPLETING", "SUSPENDED"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job-id", required=True)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--cluster", default="zj225@slurmc.ie.cuhk.edu.hk")
    ap.add_argument("--max-wait-seconds", type=int, default=8 * 60 * 60)
    args = ap.parse_args()
    outdir = args.outdir.expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(outdir, 0o700)
    logpath = outdir / "driver.log"
    started = time.monotonic()
    running_since = None

    def note(message: str) -> None:
        line = time.strftime("%Y-%m-%dT%H:%M:%S%z ") + message
        print(line, flush=True)
        with logpath.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        os.chmod(logpath, 0o600)

    def stop_owned_job() -> None:
        # Exact job ID submitted for this evaluation; do not use a pattern.
        run(["ssh", "-o", "BatchMode=yes", args.cluster,
             f"scancel {args.job_id}"], timeout=20)

    def release_on_signal(signum, _frame) -> None:
        note(f"signal={signum}; releasing_exact_owned_job")
        stop_owned_job()
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, release_on_signal)
    signal.signal(signal.SIGTERM, release_on_signal)

    note(f"waiting_for_slurm_job={args.job_id}")
    while time.monotonic() - started < args.max_wait_seconds:
        q = run(["ssh", "-o", "BatchMode=yes", args.cluster,
                 f"squeue -h -j {args.job_id} -o %T"], timeout=20)
        if q.returncode != 0:
            # Slurm commonly returns nonzero plus "Invalid job id" after a
            # job has left the queue. Consult accounting before treating this
            # as a transient SSH/controller failure, otherwise the watcher can
            # retry forever after its exact job has already failed or ended.
            acct = run(["ssh", "-o", "BatchMode=yes", args.cluster,
                        f"sacct -n -X -j {args.job_id} --format=State"], timeout=20)
            terminal = accounting_state(acct.stdout) if acct.returncode == 0 else "unknown"
            if is_terminal_state(terminal):
                note(f"slurm_job_not_in_queue_state={terminal}; no_model_prompts_sent")
                return 3
            note("temporary_slurm_poll_error; will_retry_without_changing_job")
            time.sleep(30)
            continue
        state = q.stdout.strip().splitlines()[0] if q.returncode == 0 and q.stdout.strip() else ""
        if state == "RUNNING":
            if running_since is None:
                running_since = time.monotonic()
                note("reference_allocation_running; waiting_for_both_local_health_checks")
            ready = run(["ssh", "-o", "BatchMode=yes", args.cluster,
                         f"grep -Fq reference_servers_ready=true $HOME/cyber-model-migration/phase107-runtime/logs/phase107-refs-{args.job_id}.out"], timeout=20)
            if ready.returncode == 0:
                note("both_reference_servers_and_loopback_tunnels_ready; starting_blind_collection")
                collector = args.repo / "training/eval/phase107_collect_blind.py"
                cases = args.repo / "training/eval/phase107-private-cases-v0.2.json"
                cmd = [sys.executable, str(collector), "--cases", str(cases), "--outdir", str(outdir)]
                try:
                    with logpath.open("a", encoding="utf-8") as log:
                        rc = subprocess.run(cmd, cwd=args.repo, stdout=log, stderr=subprocess.STDOUT).returncode
                    note(f"blind_collection_exit={rc}")
                    return rc
                finally:
                    stop_owned_job()
                    note("released_owned_reference_job")
            if time.monotonic() - running_since > 30 * 60:
                note("reference_servers_did_not_become_ready_within_30_minutes; releasing_owned_job")
                stop_owned_job()
                return 2
        elif state in {"PENDING", "CONFIGURING", "COMPLETING"}:
            pass
        elif state:
            note(f"slurm_job_terminal_state={state}; no_model_prompts_sent")
            return 3
        else:
            acct = run(["ssh", "-o", "BatchMode=yes", args.cluster,
                        f"sacct -n -X -j {args.job_id} --format=State"], timeout=20)
            terminal = accounting_state(acct.stdout) if acct.returncode == 0 else "unknown"
            note(f"slurm_job_not_in_queue_state={terminal}; no_model_prompts_sent")
            return 4
        time.sleep(30)
    note("wait_timeout; releasing_exact_owned_job_to_avoid_idle_GPU_allocation")
    stop_owned_job()
    return 5


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("driver interrupted; Slurm job remains in its prior state", file=sys.stderr)
        raise SystemExit(130)
