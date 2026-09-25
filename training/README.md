# 本地网安模型训练档案

目标：在 16GB M4 Mac mini 上训练一个通过 API 接入 DeepSeek Harness 的本地网安特化模型。模型使用 Qwen3-4B MLX 4-bit 基座与 LoRA，强调专业分析、证据边界、低幻觉和对用户项目的可验证熟悉度。

## 不进入 Git 的内容

- 基座及 LoRA 权重（`*.safetensors`、`*.gguf`）
- API Token、SSH 凭据和 `.env`
- 含私人信息的原始材料
- 可由脚本重新生成的训练拆分和运行日志

## Mac mini 路径约定

### Phase108 集群后续实验状态（2026-09-26）

- Phase108 scale-corrected candidate 在学校集群的隔离目录完成训练；Slurm job `44306` 正常结束。候选目录：`/data3/ieug25/zj225/cyber-model-migration/models/phase108-cuda-recovery-scale20-corrected-20260924-r2`；最终 adapter SHA-256：`4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772`。
- 训练来源 adapter SHA-256：`3ed1a85e7b021e1498332a525bfa4bb75b336a03579d526f8210f1576317036`；manifest 记录 rank 8、MLX scale 20、PEFT alpha 160/effective scale 20、19,621 条训练行、未读取 test split。固定验证 1,089 条，candidate loss 1.70626，对照 parent loss 1.73623；这是 token-loss 结果，不能单独证明生成能力或网安专业能力提升。
- 功能诊断尚未闭环：已暴露的 v0.9 题面上 parent 与 candidate 都出现 16/16 空输出；4 条公开开发探针两者均正常输出。它们都不是有效盲测分数，不能据此晋级。
- v0.3–v0.9 题库不可作为新鲜独立盲测：存在场景重复或既往暴露。v0.3 生成器还缺少全局 `scenario_root_id`，仅用类别/序号构造唯一 family 字符串；不要给旧行补随机 ID 规避预检。新题库必须先重建真实场景根，再完成污染/近重复扫描与独立语义审查。
- 集群最近只读核验：无 Phase108 作业；`/data3` 为 280G/479G（58.5%）。生产 API/adapter、评分 rubric、推理 protocol 和工具权限未更改。详细来源与历史失败见 [Phase108 scale-correction journal](journal/2026-09-25-phase108-validation-scale-fix.md) 和 [预检加固记录](journal/2026-09-26-phase108-suite-preflight-hardening.md)。

### 最近一次 Mac mini 实机核验（2026-09-20 16:25 HKT；之后未重新检查）

- 主机：`jiehan@192.168.31.212`；生产 API 端口 `18765`。
- Phase 91 生产链路的基座：`/Users/jiehan/models/Qwen3-4B-mlx-4bit-phase3-wrapper`。
- 实际生产 adapter：`/Users/jiehan/models/phase99-multiturn-candidate/adapters.safetensors`，SHA-256 `bfb6901a7aef2c4e5c3b9166a3f0bd982ca7b6ee461ea3e81a6f9a42fe05e37c`。Phase 91 是服务/评测基线名称，adapter 目录中的 Phase 99 是实际加载的权重版本，两者不能互相替代。
- 正在训练：Phase 108，PID `43774`，输出 `/Users/jiehan/models/phase108-cleanv2-epoch1-20260920`；截至核验最新报告为第 600/19,621 步，尚未到第一个 1,000 步权重保存点。
- 训练日志：`/Users/jiehan/cyber-agent/phase108-cleanv2-epoch1.log`；可复现配置：[phase108_cleanv2_epoch1.yaml](configs/phase108_cleanv2_epoch1.yaml)。进程退出不等于成功，须核对最终日志、权重、验证与测试结果。
- Phase 107 的 320 题三方评测已完成；结果尚不支持同档能力结论。参考是 GPT-OSS 20B 和 Gemma 4 26B，其中 Gemma 可评分覆盖不足；不能据此声称追平顶尖商业模型。详见[当日日志](journal/2026-09-20-phase107-collection.md)的 final outcome。
- Phase 108 尚无能力评测或部署批准。旧 Phase 107 题库可用于明确标注的重复回归；新的盲测须处理既有审阅者已见过题目和已揭盲的问题。测试集不得用于选择 checkpoint。

以上为带时间戳的快照；恢复任务时重新核查 PID、日志、实际服务配置和 adapter 哈希。此前路径保留如下，仅用于追溯旧实验。

### 历史路径（不是当前部署配置）

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
- 历史在线适配器：`~/models/qwen-cyber-adapter-phase5-best120`（指向 phase5 step 120）
- 工作目录：`~/cyber-agent`
- 原始纯净拆分：`~/datasets/cybersec-clean`

## 恢复方式

将 `training/scripts/` 和 `training/configs/` 同步到 Mac mini 的 `~/cyber-agent/`，运行数据生成脚本，然后使用：

```bash
~/venvs/agents-a1/bin/python -m mlx_lm lora --config phase3_grounded.yaml
```

每一阶段的实际结果、失败项和检查点选择记录在 `training/journal/`。

历史部署状态（2026-09-04）：phase6 与 phase7 均未通过裸权重盲评门槛，不部署；
当时在线 API 使用相对更稳的 phase5-step120，并由句段级证据守门、
工具调用协议转换和 LaunchAgent 提供运行时兜底。它适合继续测试，仍不代表
已达到最终生产质量。该阶段评测见
`training/eval/phase7-completion-and-api-report-2026-09-04.md`。
