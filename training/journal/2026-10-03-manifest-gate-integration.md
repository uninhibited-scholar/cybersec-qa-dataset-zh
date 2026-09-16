# Manifest gate integration — 2026-10-03

The candidate approval checker now requires the evaluated candidate's
`candidate-manifest.json` and verifies every recorded file hash before it can
report eligibility. A changed file set or hash adds a rejection reason.

The checker remains non-mutating, still requires the independent blind,
tool, trajectory, and manual-review gates, and cannot switch the production
adapter. Both scripts pass syntax checks and expose the new required
arguments.
