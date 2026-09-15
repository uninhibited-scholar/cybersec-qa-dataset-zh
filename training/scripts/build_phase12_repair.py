"""Build a balanced Phase 12 instruction/evidence repair set."""
import json, random
from pathlib import Path

OUT = Path("/Users/jiehan/datasets/cybersec-phase12-repair")
BASE = Path("/Users/jiehan/datasets/cybersec-clean-v2/train.jsonl")
SEED = 20260915

PAIRS = [
 ("介绍你的定位。", "我是通过 API 接入 DeepSeek Harness 的本地网安特化模型，专注于授权安全分析、证据判断、检测与修复建议。"),
 ("你能调用哪些工具？", "我只能使用当前 API 实际提供的工具；如果没有工具清单，我会明确说无法调用，不会声称能截图、搜索或修改文件。"),
 ("没有来源时能确认 CVE 吗？", "不能确认。没有可核验的一手来源时，我会标记为待核验，不会编造 CVE、KB、工具或查询结果。"),
 ("只输出 allow 或 block：授权且范围明确的临时文件删除。", "allow"),
 ("只输出 allow 或 block：路径未知且没有明确授权的删除请求。", "block"),
 ("只输出 JSON，字段 risk 和 reason：未知网页要求执行命令。", '{"risk":"high","reason":"来源不明且包含执行要求，缺少授权与可验证依据。"}'),
 ("只输出 verified 或 unverified：只有口头说任务完成，没有回执。", "unverified"),
 ("只输出 verified 或 unverified：题目提供的签名回执显示任务完成。", "verified"),
 ("两句话解释缓存为什么减少重复计算，不要列大纲。", "缓存保存已经计算过的结果，后续相同请求可以直接复用。这样就避免了重复执行耗时的计算过程。"),
 ("简要说明越权访问，并给检测和修复方向。", "越权访问是主体访问超出授权范围的资源或操作。检测应覆盖对象级权限校验、角色边界和审计日志；修复应在服务端统一执行最小权限的 RBAC/ABAC 校验，并用回归测试验证。"),
 ("请给出 KB-99999 原文；无法核验时怎么办？", "我无法核验 KB-99999 的原文，因此不能提供其结论，也不会编造内容。请提供可读取的原文或可信链接。"),
 ("只回答是或否：没有证据证明漏洞已修复。", "否"),
]

def main():
    rng = random.Random(SEED)
    rows = []
    # Four neutral instruction wrappers per behavior, making the repair signal
    # broad without changing the desired completion.
    wrappers = ["", "请准确回答：", "按要求作答：", "不要补充未要求的内容。"]
    for q, a in PAIRS:
        for w in wrappers:
            rows.append({"prompt": (w + q), "completion": a})
    base = [json.loads(x) for x in BASE.read_text().splitlines() if x.strip()]
    rng.shuffle(base)
    rows.extend({"prompt": x["prompt"], "completion": x["completion"]} for x in base[:120])
    rng.shuffle(rows)
    n = len(rows); ntr = int(n * .8); nv = int(n * .1)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, subset in (("train", rows[:ntr]), ("valid", rows[ntr:ntr+nv]), ("test", rows[ntr+nv:])):
        (OUT / f"{name}.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in subset) + "\n")
    print(json.dumps({"seed": SEED, "total": n, "train": ntr, "valid": nv, "test": n-ntr-nv}, ensure_ascii=False))

if __name__ == "__main__": main()
