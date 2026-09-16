# Phase 81 clean-candidate report

- Scope: isolated candidate only; production API and phase5-best120 unchanged.
- Base: `Qwen3-4B-mlx-4bit-phase3-wrapper`.
- Start adapter: clean production `qwen-cyber-adapter-phase5-best120/adapters.safetensors`.
- Data: audited 7/1/1 messages-format examples covering ordinary facts, short formats, evidence boundaries, and defensive SSRF guidance.
- Audit: passed; no private markers, attack payloads, system/template residue, or real project data.
- Training: LoRA, 4 layers, 16 iterations, learning rate 5e-8, max sequence 2048, batch 1.
- Validation loss: 3.128 at iter 1 and iter 16; train loss 3.359 at iter 16; peak memory 2.539 GB; finished cleanly.
- Checkpoints: `~/models/phase81-clean-20260917/0000004_adapters.safetensors`, `0000008`, `0000012`, `0000016`, plus final `adapters.safetensors`.

This is a candidate checkpoint, not a production deployment. Behavioral regression and blind evaluation are required before any promotion.
