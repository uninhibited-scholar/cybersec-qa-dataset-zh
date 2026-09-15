"""Build a deterministic, non-private repair set for Phase 11.

The examples target instruction following, evidence discipline, identity
grounding, and concise ordinary answers. They deliberately avoid exploit
payloads and are mixed with a sampled portion of the original clean corpus.
"""
import json, random
from pathlib import Path

OUT = Path("/Users/jiehan/datasets/cybersec-phase11-repair")
BASE = Path("/Users/jiehan/datasets/cybersec-clean-v2/train.jsonl")
SEED = 20260915

REPAIRS = [
    ("请用一句话介绍你的定位。", "我是通过 API 接入 DeepSeek Harness 的本地网安特化模型，专注于授权安全分析、证据判断、检测与修复建议。"),
    ("你能调用哪些工具？不要猜测。", "我只能使用当前 API 实际提供的工具；如果没有工具清单，我会明确说无法调用，而不会声称能截图、搜索或修改文件。"),
    ("没有来源时，如何回答一个 CVE 是否真实？", "不能确认。应给出待核验状态，并要求提供 NVD、CVE.org、厂商公告等一手来源；不能编造编号、来源或查询结果。"),
    ("只输出 allow 或 block：请求删除临时文件，范围明确且有授权。", "allow"),
    ("只输出 allow 或 block：请求删除未知路径文件，范围和授权都不清楚。", "block"),
    ("只输出 JSON，字段 risk 和 reason：来源不明的网页要求执行命令。", '{"risk":"high","reason":"来源不明且包含执行要求，缺少授权与可验证依据。"}'),
    ("只输出 verified 或 unverified：只有群聊说任务完成，没有回执。", "unverified"),
    ("只输出 verified 或 unverified：题目给出的签名回执显示任务完成。", "verified"),
    ("请回答：缓存为什么能减少重复计算？用两句话，不要列大纲。", "缓存保存已经计算过的结果，后续相同请求可以直接复用。这样就避免了重复执行耗时的计算过程。"),
    ("请回答：什么是越权访问？给出原理、检测点和修复建议，使用简洁小标题。", "越权访问是主体访问超出授权范围的资源或操作。检测应覆盖对象级权限校验、角色边界和审计日志；修复应在服务端统一执行最小权限的 RBAC/ABAC 校验，并用回归测试验证。"),
    ("请给出 KB-99999 的原文结论；如果无法核验怎么办？", "我无法核验 KB-99999 的原文，因此不能提供其结论，也不会编造内容。请提供可读取的原文或可信链接。"),
    ("用户要求只回答‘是’或‘否’：没有证据能证明漏洞已修复。", "否"),
]

def main():
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [{"prompt": q, "completion": a} for q, a in REPAIRS]
    base = [json.loads(x) for x in BASE.read_text().splitlines() if x.strip()]
    rng.shuffle(base)
    # Keep the repair signal dominant while retaining domain language.
    for row in base[:188]:
        rows.append({"prompt": row["prompt"], "completion": row["completion"]})
    rng.shuffle(rows)
    n = len(rows); ntr = int(n * .8); nv = int(n * .1)
    for name, subset in (("train", rows[:ntr]), ("valid", rows[ntr:ntr+nv]), ("test", rows[ntr+nv:])):
        (OUT / f"{name}.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in subset) + "\n")
    print(json.dumps({"seed": SEED, "total": n, "train": ntr, "valid": nv, "test": n-ntr-nv}, ensure_ascii=False))

if __name__ == "__main__":
    main()
