# Phase 107 matched inference protocol v0.1 — draft

This is an execution-protocol draft only. It does not freeze the rubric, send benchmark prompts, score outputs, or change the Phase 91 deployment.

## Phase 91 runtime facts

Read-only inspection on 2026-09-19 confirmed that the deployed API uses `phase91_worker.py` (SHA-256 `a4936301d54bb08bf8b7fa82847e090bbba827c6815513dd5d2d3ae88f7302cb`), Qwen3-4B phase3-wrapper plus `phase99-multiturn-candidate`, and port 18765.

The worker ignores incoming Harness `system` messages and installs its own fixed system message. With no tools, its effective system content is:

> 你是运行在用户 Mac mini 上、通过 API 接入 DeepSeek Harness 的本地网安特化语言模型。严格区分模型、知识库和外层工具；不得虚构未接入、未执行或未返回结果的能力。正常回答用户提出的分析问题；证据不足时指出具体未知项，但不要用固定拒答替代可完成的文本分析。默认使用清晰 Markdown：先给结论，再按必要的小标题和要点展开；避免重复、空泛套话和过深层级。不要复述格式指令，也不要把长篇正文塞进工具参数。严禁编造上下文未提供的日志、指标、文件、函数、错误结构、百分比、测试次数或编号；没有证据的细节必须明确写为未知；普通知识、数学、历史和地理问题可以直接回答，不要套用网安拒答模板。结构化长答优先保证所有要求部分完整结束：每部分最多三个简洁要点，除非用户明确要求展开，总长度控制在约一千个中文字内。本轮没有向你提供工具。请只输出完整的纯文本 Markdown 回答，不得输出 `<tool_call>`、工具名或规划模式标记。

The worker's primary sampler is temperature 0.12, top-p 0.9, repetition penalty 1.12 over 128 recent tokens, with a default response budget of 700 tokens (capped at 1400). It retries once on empty output with temperature 0.7; repetitive output triggers a further retry at temperature 0.05 with a 500-token cap. Post-generation logic also applies evidence/tool-claim guards, a technical safety guard, and repetition trimming. These behaviors are part of the deployed endpoint, not the Qwen weights alone.

## Proposed matched run

- Use the exact no-tool system content above for each reference model. Phase 91 continues through its existing production API; no API configuration is changed.
- Send each case's user message or multi-turn message sequence unchanged to every system. Pass an empty tool inventory to all systems. Preserve each reference model's native GGUF chat template; do not flatten or paraphrase the case content.
- Set a 700-token output cap for every system. Match the first-pass sampling settings where supported: temperature 0.12, top-p 0.9, repetition penalty 1.12, repetition window 128. Record runtime-specific seed behavior and finish reason; the current Phase 91 worker does not expose a seed override or caller-set sampler.
- Use one fresh conversation per case and model; never carry state between cases. For multi-turn cases, send the full case conversation in order. No browsing, external tools, retrieval, or network access is enabled for inference.
- Apply the same transport timeout and parsing rules. Record time-to-first/total latency and classify empty output, truncation, timeout, parse error, and model refusal separately. Do not silently retry except for the Phase 91 worker's existing in-process fallback; report that endpoint-specific behavior.
- Randomize system run order per case. Keep identities blinded in the response bundle until adjudication. Store raw outputs and the private answer key outside Git.

## Interpretation caveat

This compares the user-visible Phase 91 endpoint against reference model runtimes. Phase 91 has endpoint-side guards, retry logic, and post-processing that the direct llama.cpp reference path does not. Therefore, an observed advantage is an end-to-end system result, not proof that the Qwen weights alone match a larger reference. If the intended claim is raw model-weight parity, a separate wrapper-free, same-runtime experiment is required and must not be conflated with this endpoint comparison.

## Approval boundary

This protocol is a draft. Before sending any private Phase 107 cases, explicitly approve or revise this run protocol and the separate rubric draft. No scores or rankings may be generated while either remains unfrozen.
