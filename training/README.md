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
- phase6 输出：`~/models/qwen-cyber-adapter-phase6-provenance`
- phase6 评测候选：`0000060_adapters.safetensors`（负向实验，不部署）
- phase7 输出：`~/models/qwen-cyber-adapter-phase7-provenance-refine`
- phase7 评测候选：`0000080_adapters.safetensors`、`0000220_adapters.safetensors`（负向实验，不部署）
- 当前在线适配器：`~/models/qwen-cyber-adapter-phase5-best120`（指向 phase5 step 120）
- 工作目录：`~/cyber-agent`
- 原始纯净拆分：`~/datasets/cybersec-clean`

## 恢复方式

将 `training/scripts/` 和 `training/configs/` 同步到 Mac mini 的 `~/cyber-agent/`，运行数据生成脚本，然后使用：

```bash
~/venvs/agents-a1/bin/python -m mlx_lm lora --config phase3_grounded.yaml
```

每一阶段的实际结果、失败项和检查点选择记录在 `training/journal/`。

当前部署状态：phase6 与 phase7 均未通过裸权重盲评门槛，不部署；
在线 API 暂时使用相对更稳的 phase5-step120，并由句段级证据守门、
工具调用协议转换和 LaunchAgent 提供运行时兜底。它适合继续测试，仍不代表
已达到最终生产质量。最新评测见
`training/eval/phase7-completion-and-api-report-2026-09-04.md`。
