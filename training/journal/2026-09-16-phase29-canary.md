# Phase29 isolated canary

日期：2026-09-16

在 Mac mini 上以 `tmux` 启动独立 canary API：端口 `18766`，适配器为 `/Users/jiehan/models/phase29-mixed-20261023`。生产 API 仍在 `18765`，未替换适配器。

两端健康检查均返回 `ok`；同一条无害缓存问题请求，两端均返回非空回答。该 canary 只用于并行体验和后续回归，不能视为生产部署。

随后在 canary 副本的 API 层补上了“执行扫描工具/真实返回码”无工具回执规则，并复测得到确定性的证据边界拒答。生产端口 `18765` 未修改。
