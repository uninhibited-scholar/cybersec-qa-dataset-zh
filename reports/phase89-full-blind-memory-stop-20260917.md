# Phase 89 full blind run — memory safety stop

Date: 2026-09-17

The full 20-case blind run was started with the candidate isolated on port 18778. After 6 cases, available pages fell to approximately 16k while production remained healthy. Swap-in/out was still zero, but this crossed the predeclared safety threshold because the earlier watchdog panic involved severe unified-memory pressure.

The candidate API and blind runner were stopped immediately. Port 18778 is closed. Production API 18765 remained healthy throughout and returned `status: ok`; memory recovered to approximately 42k free pages.

Decision: do not run the full suite with production and candidate models resident simultaneously. The next evaluation must either stop production temporarily under an explicit maintenance window, or use a lower-memory/serialized inference path.
