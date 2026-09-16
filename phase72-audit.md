# Phase 72 candidate gate audit

- Scope: candidate wrapper only; no training and no production service.
- Phase 71 failure classes: SSRF output included an internal IP, lateral
  movement and data theft language; tool-result answer retained formatting
  residue; ordinary fact answer contained an inaccurate extra claim.
- New hard gate: candidate output containing internal-address literals,
  lateral-movement or theft wording is rejected, even if surrounded by
  defensive wording.
- Regression tests: 8/8 passed.
- Ordinary-fact accuracy remains a model-quality regression requirement; the
  wrapper does not invent or rewrite factual answers.
