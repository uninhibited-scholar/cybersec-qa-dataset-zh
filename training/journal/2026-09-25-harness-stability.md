# Harness 稳定性基线：CPU 回退

日期：2026-09-25

## 架构判断

基础模型的权重能力只是最终表现的一部分。Harness 的上下文组装、模型路由、超时/回退、输出协议和运行可观测性会直接影响调用方实际拿到的结果。Kimi Code 这种把模型调用和工作流外壳结合起来的方式值得研究；本项目继续保持基座、adapter、Harness、路由和离线更新模块独立。

## 实测

- 集群路由脚本语法通过。
- 作业 44501：大模型端点不可用时，路由正确退回 CPU Qwen3-1.7B，并返回 OpenAI 兼容 JSON。但模型把 `<think>` 思考通道文本放进了面向用户的内容，所以初次 smoke 仅证明了路由，不算响应质量通过。
- 检查 Qwen3-1.7B tokenizer 配置，确认 chat template 支持 `enable_thinking=False`。
- CPU fallback 服务现已以该参数渲染聊天模板；健康轮询的预期启动错误也被静默处理。
- 作业 44504：`COMPLETED`, exit `0`。健康结果为 `big=false, small=true`；请求路由标记 `small_fallback`；返回 `The fallback test has been confirmed.`，8 个 completion tokens，推理耗时约 3.23 秒；响应无 `<think>` 标记；最终 `DUAL_ROUTER_SMOKE=PASS`。
- 生产端口 18765 未被调用或修改。

## 文件变更

- `training/scripts/cpu_small_model_server.py`：生成时关闭 Qwen3 思考通道。
- `training/slurm/dual_router_smoke.sbatch`：验证回退响应非空且不泄露思考通道，并抑制启动轮询期间的预期连接错误噪声。

## 结论与后续

CPU fallback 的基本服务和响应格式现在有了实际通过证据，但仍只是服务可用性检查，不代表模型专业能力。下一步应隔离验证 Qwen3-14B BF16 的 OpenAI 兼容服务端点，再对“大模型正常路由”和“排队/不可用时 CPU 回退”分别做端到端测试。完成前不修改生产 API 或现有 adapter。
