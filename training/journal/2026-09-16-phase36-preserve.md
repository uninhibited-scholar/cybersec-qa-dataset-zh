# Phase 36 — preservation修复候选

- 目标：修复 Phase 35 对普通问答与开放式回答的空响应回归，同时保留网安专业能力、证据边界和格式遵循。
- 生产基座与起点：`Qwen3-4B-mlx-4bit-phase3-wrapper` + `qwen-cyber-adapter-phase5-best120`（只读）。
- 新数据：Phase 35 网安样本 216 条 + 中性/格式/证据边界样本 40 条，固定随机种子 36；验证/测试集各 28 条。
- 训练配置：LoRA 4 层，学习率 `5e-8`，120 steps，最大序列 2048；输出隔离于 `phase36-preserve-20260916`。
- 安全闸门：不触碰生产端口 18765；训练失败或盲测不通过时保留生产版本不变。
- 远端任务于 2026-09-16 启动，日志：`~/cyber-agent/phase36-preserve-20260916.log`。
