# Route investigation after external template-leak report

Read-only inspection of current Mac mini code, 2026-09-09.

Confirmed:
- api_server_identity.py local route passes only last_user[-12000:] into
  ~/bin/cyber-agent. Caller system messages and preceding history are omitted.
- That launcher executes ~/cyber-agent/cyber_agent.py, which hardcodes original
  Qwen3-4B-mlx-4bit and qwen-cyber-adapter, not phase5-best120 or Phase8.
- cyber_agent.py builds its own evidence/label prompt. Local route therefore
  cannot test caller system-format adherence as if those instructions arrived.
- mlx_agent_worker.py also skips role=system and injects its own Markdown
  instructions. The newer agent route is affected by system-message loss too.

The external three-case report provides evidence of bad outputs, but not proof
that training alone destroyed all instruction following. Previous API regression
tested qwen-cyber-agent, not qwen-cyber-local; do not combine their scores.

Not yet established: frequency of format-instruction leakage in source responses,
truncated target prevalence, effect of adapter versus bare base. No running
evaluation was stopped, no serving code or weights changed during this inspection.

Next repair should explicitly preserve caller instruction hierarchy, separate
retrieved evidence from instructions, and test both routes with identical messages.
Then compare base and adapter under identical serialization before retraining.
