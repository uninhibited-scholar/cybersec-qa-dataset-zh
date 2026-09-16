# Phase29 isolated canary

日期：2026-09-16

在 Mac mini 上以 `tmux` 启动独立 canary API：端口 `18766`，适配器为 `/Users/jiehan/models/phase29-mixed-20261023`。生产 API 仍在 `18765`，未替换适配器。

两端健康检查均返回 `ok`；同一条无害缓存问题请求，两端均返回非空回答。该 canary 只用于并行体验和后续回归，不能视为生产部署。

随后在 canary 副本的 API 层补上了“执行扫描工具/真实返回码”无工具回执规则，并复测得到确定性的证据边界拒答。生产端口 `18765` 未修改。

对照复测显示生产端口仍会对同一请求生成 IaC 扫描建议，未返回确定性拒答；因此 canary 的 API guard 修复不能宣称已进入生产，正式切换前必须先独立评审并验证该补丁。

批准器现已强制要求 canary API 回归报告。加入该必需闸门后，Phase29 重新检查返回 `eligible: true`、`mutated: false`；生产仍未切换。

批准器进一步加入生产 API 回归要求后，当前结果明确为 `eligible: false`（原因：生产 API 回归失败）。这阻止候选在生产端 guard 修复前被误部署。
