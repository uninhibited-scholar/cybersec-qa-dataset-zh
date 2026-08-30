# 本地网安模型训练档案

目标：在 16GB M4 Mac mini 上训练一个通过 API 接入 DeepSeek Harness 的本地网安特化模型。模型使用 Qwen3-4B MLX 4-bit 基座与 LoRA，强调专业分析、证据边界、低幻觉和对用户项目的可验证熟悉度。

## 不进入 Git 的内容

- 基座及 LoRA 权重（`*.safetensors`、`*.gguf`）
- API Token、SSH 凭据和 `.env`
- 含私人信息的原始材料
- 可由脚本重新生成的训练拆分和运行日志

## Mac mini 路径约定

- 基座：`~/models/Qwen3-4B-mlx-4bit`
- 初版 LoRA：`~/models/qwen-cyber-adapter`
- identity-v1 最佳点：`~/models/qwen-cyber-adapter-identity-v1-best75`
- identity-v2 最佳点：`~/models/qwen-cyber-adapter-identity-v2-best75`
- phase3 输出：`~/models/qwen-cyber-adapter-phase3-grounded`
- phase3 保留最佳点：`~/models/qwen-cyber-adapter-phase3-grounded-best100`
- phase4 输出：`~/models/qwen-cyber-adapter-phase4-balanced`
- phase5 输出：`~/models/qwen-cyber-adapter-phase5-corrective`
- phase6 当前父检查点：phase5 输出中的 `0000120_adapters.safetensors`
- 工作目录：`~/cyber-agent`
- 原始纯净拆分：`~/datasets/cybersec-clean`

## 恢复方式

将 `training/scripts/` 和 `training/configs/` 同步到 Mac mini 的 `~/cyber-agent/`，运行数据生成脚本，然后使用：

```bash
~/venvs/agents-a1/bin/python -m mlx_lm lora --config phase3_grounded.yaml
```

每一阶段的实际结果、失败项和检查点选择记录在 `training/journal/`。

当前部署状态：API 不切换到 phase5；phase5-step120 已改善一项技术回归，
但仍存在不受支持的历史陈述污染，尚未通过部署门槛。最新评测见
`training/eval/phase5-neutral-blind-report.md`。
