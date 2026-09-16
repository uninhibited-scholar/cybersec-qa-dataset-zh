# Phase 27 SSRF-policy training — 2026-10-17

Started and completed an isolated MLX LoRA run on the Mac mini. The initial
tmux attempt was unavailable because tmux is not installed; the job was then
started with a detached system process and verified by PID and live log.

- Base: `Qwen3-4B-official-chatml-phase10`
- Resume adapter: `phase24-depth-20260925`
- Output: `phase27-ssrf-policy-20261017`
- Iterations: 80; learning rate: `5e-10`; max sequence length: 2048
- Peak memory: about 2.96 GB
- Validation loss: 4.899
- Test loss: 4.349; test perplexity: 77.372
- Checkpoints: 40 and 80, plus final adapter

The run completed normally without NaN or crash. The production API and old
adapter were not touched. The next required step is independent behavioral
blind evaluation; training loss alone is not a deployment decision.
