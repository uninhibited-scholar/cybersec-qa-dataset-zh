# Phase 107 matched inference protocol v0.1 — draft

This is an execution-protocol draft only. It does not freeze the rubric, send benchmark prompts, score outputs, or change the Phase 91 deployment.

## Phase 91 runtime facts

Read-only inspection on 2026-09-19 confirmed that the deployed API uses `phase91_worker.py` (SHA-256 `a4936301d54bb08bf8b7fa82847e090bbba827c6815513dd5d2d3ae88f7302cb`), Qwen3-4B phase3-wrapper plus `phase99-multiturn-candidate`, and port 18765.

The worker ignores incoming Harness `system` messages and installs its own fixed system message. With no tools, its effective system content is:

> 你是运行在用户 Mac mini 上、通过 API 接入 DeepSeek Harness 的本地网安特化语言模型。严格区分模型、知识库和外层工具；不得虚构未接入、未执行或未返回结果的能力。正常回答用户提出的分析问题；证据不足时指出具体未知项，但不要用固定拒答替代可完成的文本分析。默认使用清晰 Markdown：先给结论，再按必要的小标题和要点展开；避免重复、空泛套话和过深层级。不要复述格式指令，也不要把长篇正文塞进工具参数。严禁编造上下文未提供的日志、指标、文件、函数、错误结构、百分比、测试次数或编号；没有证据的细节必须明确写为未知；普通知识、数学、历史和地理问题可以直接回答，不要套用网安拒答模板。结构化长答优先保证所有要求部分完整结束：每部分最多三个简洁要点，除非用户明确要求展开，总长度控制在约一千个中文字内。本轮没有向你提供工具。请只输出完整的纯文本 Markdown 回答，不得输出 `<tool_call>`、工具名或规划模式标记。

The worker's primary sampler is temperature 0.12, top-p 0.9, repetition penalty 1.12 over 128 recent tokens, with a default response budget of 700 tokens (capped at 1400). It retries once on empty output with temperature 0.7; repetitive output triggers a further retry at temperature 0.05 with a 500-token cap. Post-generation logic also applies evidence/tool-claim guards, a technical safety guard, and repetition trimming. These behaviors are part of the deployed endpoint, not the Qwen weights alone.

## Proposed shared-input, fixed-budget run

- Objective: compare the deployed Phase 91 endpoint with two reference systems under identical task inputs, effective no-tool system instruction, conversation history, and output budget. This is an **end-to-end system comparison**, not a claim that the Qwen weights alone match larger models.
- Keep Phase 91 on its existing production API; do not alter its service or configuration. It ignores caller-provided system messages, so the API caller should pass no competing system instruction. Use the exact effective no-tool system content above for the reference models.
- Send each case's `messages` sequence unchanged to all systems. For single-turn cases it contains one user message; for multi-turn cases it is an explicit ordered user/assistant/user transcript. `prompt` is retained only as an audit/source field and must not also be sent. Use a fresh conversation per case/model, pass an empty tool inventory, and preserve each GGUF's native chat template. No browsing, tools, retrieval, or external network access is enabled for inference.
- Apply a 700-token output ceiling to all systems (`max_tokens=700` for Phase 91 and the equivalent generation cap for references). Score only the user-visible final answer; do not expose or score hidden reasoning traces.
- For the reference run, preserve each model's native reasoning capability (`reasoning=auto`/template default). **Do not reuse `--reasoning off` from the harmless runtime smoke as an evaluation setting**; that was only used to make the smoke produce a short visible answer. Use the shared first-pass sampler controls supported by the Phase 91 worker: temperature 0.12, top-p 0.9, repetition penalty 1.12, repetition window 128. Explicitly disable or record any additional reference-runtime samplers (such as top-k/min-p/dry sampling) so undocumented defaults do not silently differ. Record all arguments, model/template hashes, finish reasons, and seed behavior. Phase 91 has no caller seed override, so exact seed parity cannot be claimed.
- Make zero evaluator-client retries and apply identical transport timeout and response parsing. The Phase 91 worker itself has empty/repetition fallback retries, evidence/tool guards, and output post-processing; leave them enabled because this arm measures the deployed endpoint, but tag every response with the endpoint-specific path when observable and disclose this asymmetry in results.
- Record time-to-first-token and total latency. Classify empty output, truncation, timeout, parse error, and refusal separately. Randomize system run order per case; blind model identities until adjudication. Keep raw outputs and answer keys outside Git.

## Interpretation caveat

This compares the user-visible Phase 91 endpoint against reference model runtimes with shared task/system inputs and a fixed output ceiling. Phase 91 has endpoint-side guards, retry logic, and post-processing that the direct llama.cpp reference path does not, and Phase 91 cannot be assigned the same RNG seed. Therefore, this protocol can support an end-to-end system comparison with disclosed runtime asymmetries, but not a strict sampler-matched causal claim or proof that the Qwen weights alone match larger references. If a raw model-weight comparison is later desired, it needs a separate wrapper-free, same-runtime experiment and a separately documented protocol.

## Approval boundary

This protocol is a draft. Before sending any private Phase 107 cases, explicitly approve or revise this run protocol and the separate rubric draft. No scores or rankings may be generated while either remains unfrozen.
