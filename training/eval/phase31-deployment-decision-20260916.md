# Phase 31 deployment decision — 2026-09-16

## Decision

**保留为隔离候选，不切换生产。**

## Evidence

- 训练完成，适配器独立保存；基座和生产适配器未修改。
- 8 项 worker policy 回归及扩展 12 项回归均有输出；身份、严格格式、证据边界、工具回执正反例通过。
- 自动部署闸门测试 2/2 通过，生产健康端点正常。
- 质量复核发现短回答曾出现英文残留，已在隔离 worker 做最小清理；权重未改动。
- 认证 API 冒烟检查因缺少环境提供的 `CYBER_API_TOKEN` 按设计停止，不能据此宣称认证链路已验证。

## Remaining gates

1. 在安全注入 token 后完成认证 API 回归（token 不写入仓库、不打印）。
2. 用独立短问答集确认专业内容不会被通用兜底替代。
3. 在候选、生产和基座之间做盲法质量比较，再由人工批准是否切换。

未携带凭据的 API 请求实测返回 HTTP 401 `unauthorized`，说明认证保护处于启用状态；这不替代携带真实凭据的正向回归。

## Production path audit

Mac mini 的 launchd 配置当前明确指向：

- `CYBER_MODEL_PATH=/Users/jiehan/models/Qwen3-4B-mlx-4bit-phase3-wrapper`
- `CYBER_ADAPTER_PATH=/Users/jiehan/models/qwen-cyber-adapter-phase5-best120`
- API port `18765`

因此生产服务当前是旧的 Phase 3/Phase 5 链路，并非 Phase 31/33 候选。该差异解释了候选盲测与生产 API 行为可能不一致；在没有单独完成候选认证回归、回滚演练和人工批准前，不得修改 launchd 配置。

任何候选更新只能提出版本，不能自动批准上线或扩大工具权限。
