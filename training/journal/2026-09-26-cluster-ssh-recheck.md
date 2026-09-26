# Cluster SSH recheck — 2026-09-26

## Purpose

Resume the isolated cluster-serving path before further model evaluation. This
is a connectivity diagnosis only; no Slurm job was submitted, cancelled, or
modified, and no production API, adapter, evaluation protocol, or permissions
were changed.

## Current observations

- GlobalProtect processes (`GlobalProtect` and `PanGPS`) were present.
- Route lookup for `172.16.5.179` selected `utun11`, whose point-to-point address
  was `198.18.0.1`.
- DNS lookup for `slurmc.ie.cuhk.edu.hk` returned no host record in the local
  resolver. An explicit query to the configured resolver did not establish a
  trustworthy login-node address; the returned `198.18.0.4` is not used.
- TCP connect to `172.16.5.179:22` succeeded, but OpenSSH reported
  `kex_exchange_identification: Connection closed by remote host` before host
  key exchange or account authentication. This is not evidence of a bad key or
  account password.
- `scutil --nc list` reported Tailscale as connected; GlobalProtect was visible
  as a running process and its tunnel interface existed. Neither observation
  proves that the campus VPN session is authenticated/healthy end-to-end.
- Since SSH could not reach an authenticated session, current Slurm state for
  service job `44601`, fixed-validation job `44593`, quota, and remote artifacts
  remains **unknown**. Historical records are not substituted for a fresh
  scheduler check.

## Follow-up after VPN UI inspection

- The GlobalProtect UI initially showed `Disconnected` / `连接已中断`, despite
  the running process and residual `utun11` route. This corrects the earlier
  inference that the campus VPN was active based on process/interface alone.
- On a later UI refresh GlobalProtect showed `Connected` to `IENet_GW`, and the
  campus hostname resolved to `172.16.5.179`.
- With that reported-connected state, TCP/22 accepted a connection but SSH was
  again closed before key exchange (`kex_exchange_identification`). A hostname
  SSH attempt timed out. Thus DNS/VPN state improved, but no authenticated SSH
  session or scheduler data was obtained; the remaining failure is at or before
  the SSH server's handshake, not an observed account-key rejection.
- No credentials were entered and no scheduler command reached the cluster.

## Next safe step

Re-establish a verified SSH handshake to the login node, then immediately read
`squeue`, `sacct` for known job IDs, quota, and the existing service run
directory. Do not resubmit the service until authoritative state confirms the
old job is terminal. Keep the service loopback-only on the allocated compute
node and use a verified SSH tunnel; never run inference on the login node.

## Work-order correction

The earlier 30-second API jobs were smoke tests and stopped with their Slurm
allocations. A prepared 48-hour service script and an old pending-job record do
not establish a usable deployment. The serving path must be confirmed
end-to-end before this workstream is described as available; Phase108 candidate
qualification remains a separate gate.
