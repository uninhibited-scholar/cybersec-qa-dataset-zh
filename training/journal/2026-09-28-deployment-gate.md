# 2026-09-28 — candidate deployment gate

Added a non-mutating approval script that checks the expanded blind suite,
forbidden-pattern count, positive and negative tool-permission tests, candidate
directory, production rollback source, and an explicit independent manual
review flag. The script only emits an eligibility decision; it never copies,
renames, reloads, or activates an adapter.

This preserves the self-evolution invariant: a candidate can propose an update,
but cannot approve itself or expand tool permissions.
