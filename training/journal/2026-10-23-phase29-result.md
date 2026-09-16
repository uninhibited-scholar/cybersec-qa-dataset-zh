# Phase 29 mixed replay result — 2026-10-23

Phase 29 mixed professional and format replay training completed from Phase
27. The professional set remained dominant while 48 format samples were
added, preventing the Phase 28 catastrophic forgetting pattern.

- Training split: 176; validation: 28; test: 28
- Iterations: 80; learning rate: `2e-10`
- Validation loss: `5.220`
- Test loss: `4.517`; test perplexity: `91.605`
- Full 12-case blind suite: **12/12**, **0 forbidden hits**

The candidate retained SSRF, evidence, tool, history and ordinary-answer
behavior while preserving the format improvements. It remains isolated and
has not been deployed.
