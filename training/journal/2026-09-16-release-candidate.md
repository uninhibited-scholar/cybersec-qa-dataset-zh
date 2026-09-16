# Phase29 release candidate

Phase29 的模型、适配器、Harness、canary API guard 补丁及回归证据已绑定到 `phase29-release-candidate.json`。候选在 canary 上通过盲测和 API 回归，但生产 API 仍未通过同一回归，因此状态明确为 `not_deployed`。

任何正式切换都必须先应用已审计的 guard 补丁、重新生成生产回归报告、通过批准器和回滚检查；本清单本身不构成部署授权。
