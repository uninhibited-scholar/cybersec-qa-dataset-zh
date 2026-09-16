# Phase 28 format repair — 2026-10-22

Phase 28 trained 60 steps from Phase 27 on 120 format-focused samples.
Training completed normally and saved checkpoints, but metrics were poor:
validation loss 6.798, test loss 6.390, test perplexity 596.086.

Behavioral spot checks showed the format goals improved (single-word and
strict JSON responses were correct, and ordinary caching remained coherent),
but a direct SSRF prompt returned an empty answer. This is a material
professional-capability regression, so Phase 28 is rejected and will not be
deployed. Phase 27 remains the best isolated candidate.
