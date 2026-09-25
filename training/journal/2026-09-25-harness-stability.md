# Harness 稳定性基线：CPU 回退

日期：2026-09-25

## 架构判断

基础模型的权重能力只是最终表现的一部分。Harness 的上下文组装、模型路由、超时/回退、输出协议和运行可观测性会直接影响调用方实际拿到的结果。Kimi Code 这种把模型调用和工作流外壳结合起来的方式值得研究；本项目继续保持基座、adapter、Harness、路由和离线更新模块独立。

用户补充的研究判断：模型能力输出值与外壳架构高度相关；Kimi Code 的调用/编排架构是值得借鉴的对象。将其作为架构假设与配置方向记录，而非已经验证的能力结论。后续优先验证路由稳定性、上下文/消息格式、SSE 流式输出、超时处理、回退透明性和可观测性；只有这些稳定后，再比较 Harness 对任务完成质量的实际影响。

稳定性优先原则：配置阶段先保证主模型、CPU 回退模型和统一 API 的健康检查、模型列表、非流式/流式请求、错误状态与路由标记都可靠；主模型排队或不可用时，必须明确告知走了小模型回退，不能让较弱模型的结果伪装成主模型输出。该 API 烟测与专业能力评测分开记录，服务链路通过不能据此宣称网安能力提升。

## 实测

- 集群路由脚本语法通过。
- 作业 44501：大模型端点不可用时，路由正确退回 CPU Qwen3-1.7B，并返回 OpenAI 兼容 JSON。但模型把 `<think>` 思考通道文本放进了面向用户的内容，所以初次 smoke 仅证明了路由，不算响应质量通过。
- 检查 Qwen3-1.7B tokenizer 配置，确认 chat template 支持 `enable_thinking=False`。
- CPU fallback 服务现已以该参数渲染聊天模板；健康轮询的预期启动错误也被静默处理。
- 作业 44504：`COMPLETED`, exit `0`。健康结果为 `big=false, small=true`；请求路由标记 `small_fallback`；返回 `The fallback test has been confirmed.`，8 个 completion tokens，推理耗时约 3.23 秒；响应无 `<think>` 标记；最终 `DUAL_ROUTER_SMOKE=PASS`。
- 为接入代码 Agent 所需的 SSE 与 `/v1/models`，新增 CUDA Transformers 后端和双模型端到端隔离 smoke；本地编译与 shell 语法检查通过，脚本 SHA-256 已在集群核对一致。
- 复核烟测时发现 14B 后端此前只实现非流式 JSON，而排队中的脚本已请求 SSE；本地 `py_compile` 也发现主服务一处缩进错误。为避免把兼容性失败带到 GPU 队列，在隔离后端补上 Transformers `TextIteratorStreamer` SSE 实现，并令烟测分别覆盖两模型的流式/非流式路径。
- 新增不依赖模型权重的 router 协议单测：大模型正常流式与非流式、主路由连接失败后的 CPU fallback、流协议不匹配时返回 502 且不伪装成 fallback；4/4 通过。Python 编译、SBATCH shell 语法和 diff 检查通过。
- 原 44505 作业已被旧 smoke 脚本标记为 superseded；如它仍在排队，先取消再以修正版提交。旧作业不作为 API 稳定性证据。
- 14B BF16 模型索引 SHA-256 与之前下载核验一致：`62d7ad35757bae5e7baa452cb1483178b7daa50e869e923226b8da10871f7ebc`。
- 生产端口 18765 未被调用或修改。

## 当前闸门

1. 取消仍排队的旧 44505，并只提交一个修正版隔离 smoke；不为绕开队列重复提交。
2. 验证 `/health`、`/v1/models`、主模型 OpenAI Chat Completions（含 SSE）和明确触发的小模型回退（含 SSE）。
3. 核验返回的模型/路由标记、非空输出、错误语义、SSE 结束帧、断连清理与日志；主模型服务失败时不得报成功或静默冒充。
4. 只有隔离烟测通过后，才整理 Kimi Code 客户端接入参数；生产端口/API 与 Phase108 adapter 继续保持不变，接入前先验证鉴权、并发、超时和资源清理。
5. 后续再用固定任务集单独评估 Harness 对任务质量的贡献，不与模型权重/adapter 的能力结论混为一谈。

## 文件变更

- `training/scripts/cpu_small_model_server.py`：生成时关闭 Qwen3 思考通道。
- `training/scripts/qwen_gpu_model_server.py`：隔离 CUDA Transformers OpenAI 服务，支持非流式 JSON 和 SSE。
- `training/scripts/dual_model_router.py`：上游 SSE 断流时以流内错误终止，避免错误地开始第二个响应并隐藏模型来源。
- `training/scripts/test_dual_model_router.py`：无需模型权重的 router 协议测试。
- `training/slurm/qwen14b_dual_api_smoke.sbatch`：隔离端到端 smoke 覆盖两个模型的流式和非流式调用。
- `training/slurm/dual_router_smoke.sbatch`：验证回退响应非空且不泄露思考通道，并抑制启动轮询期间的预期连接错误噪声。

## 结论与后续

CPU fallback 的基本服务和响应格式现在有了实际通过证据，但仍只是服务可用性检查，不代表模型专业能力。作业 44505 会验证 Qwen3-14B BF16 的 OpenAI 兼容服务端点，并测试“大模型正常路由”和“排队/不可用时 CPU 回退”。完成前不修改生产 API 或现有 adapter。
