# Architecture gate integration — 2026-10-10

Candidate approval now requires an architecture audit report in addition to
blind, tool, trajectory, and manifest reports. The report must prove that the
base model, candidate adapter and Harness are separate and that production
was not mutated.

The missing-report regression now returns a structured rejection that names
the architecture gate as well as the other absent gates. No deployment or
file mutation occurs.
