# Phase 29 approval dry run

日期：2026-09-16

在 Mac mini 上对 `phase29-mixed-20261023` 执行候选批准链的非变更检查。盲测、工具权限、离线自进化轨迹和架构隔离检查均通过；批准器唯一返回的阻断项是未记录独立人工复核。

随后完成了独立复核记录。影子对比使用较弱系统提示重新检查相同能力，发现未提供来源的 CVE 出现外部数据库式断言，且无工具回执请求出现空答。因此早先仅基于严格系统提示的 `eligible: true` 结论被新的影子回归否决；候选保持隔离，`/Users/jiehan/models/qwen-cyber-adapter` 未被修改，生产 API 未切换。

同时已在 Mac mini 用户目录安装 `tmux 3.5a`（`/Users/jiehan/.local/bin/tmux`），并验证 detached session 可创建与清理，后续长任务可在 SSH 断线后继续。
