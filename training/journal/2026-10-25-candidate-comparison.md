# Candidate comparison — 2026-10-25

Compared the recent isolated candidates using both metrics and behavior:

- **Phase 27:** test perplexity 77.372, 12/12 blind, retained;
- **Phase 28:** test perplexity 596.086 and empty SSRF response, rejected;
- **Phase 29:** test perplexity 91.605, 12/12 blind, extended format checks
  passed, selected as the best current candidate.

Phase 29 is not automatically deployed. The comparison is recorded in
`training/eval/candidate-comparison-2026-10-25.json`; production remains on
the old adapter until the complete approval and manual-review process is
explicitly satisfied.
