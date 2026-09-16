# Canary chain follow-up — 2026-09-16

The active canary API was verified on port 18766 with a separate API/worker
process chain. The worker guard was tightened for the exact “没有提供公告” CVE
variant (including impact-version questions). After restarting only the canary,
the API returned a deterministic unknown response. Production port 18765 and
its adapter were not restarted or changed.
