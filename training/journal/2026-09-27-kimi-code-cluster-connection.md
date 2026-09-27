# Kimi Code cluster connection — 2026-09-27

Kimi Code 2.0.2 now has a separate OpenAI-compatible provider named `cluster`
and model alias `cluster/qwen3-14b-bf16`. The existing managed Kimi provider and
default model were preserved. The provider targets the authenticated local
tunnel at `http://127.0.0.1:19002/v1` and reads its key from the environment
variable `CLUSTER_MODEL_API_TOKEN`; no token is stored in this repository.

The Desktop launcher `start-kimi-cluster.sh` reads the permission-600 token
file, checks the local tunnel health, exports the variable, and starts Kimi
with the cluster model alias. A real non-interactive call succeeded with
`KIMI_CLUSTER_OK`.

Kimi Code always includes its tool catalog in requests. The cluster model
endpoint has no tool executor, so the authenticated gateway now strips tool
metadata (`tools`, `functions`, and related selection fields) before forwarding
text requests. It does not claim tool support or execute tools. Gateway unit
tests remain 5/5 passing after this change; the route header still identifies
the primary or CPU fallback backend.

This validates Kimi Code text-model integration, not agent tool execution or
cybersecurity capability. The cluster service and tunnel remain bounded by
the Slurm allocation and must be re-established after allocation expiry or a
network interruption.
