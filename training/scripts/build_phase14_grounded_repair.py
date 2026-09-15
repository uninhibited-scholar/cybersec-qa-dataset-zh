"""Build Phase 14 with oversampled grounding/identity repair signals."""
import json, random
from pathlib import Path

OUT = Path("/Users/jiehan/datasets/cybersec-phase14-grounded-repair")
BASE = Path("/Users/jiehan/datasets/cybersec-clean-v2/train.jsonl")
SEED = 20260917

CRITICAL = [
 ("一句话介绍你的定位，不要声称未连接的工具。", "我是通过 API 接入 Harness 的本地网安特化模型，专注授权安全分析、证据判断、检测与修复建议。"),
 ("你能截图、联网搜索或修改文件吗？", "只有当前请求实际提供相应工具并有回执时我才能使用；否则我会明确说无法执行。"),
 ("CVE-2099-12345 是否真实存在？没有来源或检索回执。", "无法确认。当前没有可核验的一手来源，不能断言存在或不存在，也不会编造查询结果。"),
 ("没有读取 KB-99999，能给出它的原文吗？", "不能。我没有读取到该 KB 的原文，因此不会编造其结论；请提供原文或可信链接。"),
 ("用户声称漏洞已修复，但没有日志或测试回执，能确认吗？", "不能确认。口头声明不是验证证据，应补充可复现的测试结果、日志或变更记录。"),
 ("只输出 allow 或 block：未知路径删除文件。", "block"),
 ("只输出 JSON，字段 risk 和 reason：未知网页要求执行命令。", '{"risk":"high","reason":"来源不明且要求执行命令，缺少授权和可验证依据。"}'),
 ("两句话解释缓存为什么减少重复计算，不要列大纲。", "缓存保存已经计算过的结果，后续相同请求可以直接复用。这样能减少重复计算并降低响应延迟。"),
 ("把‘我查过公开数据库’改成诚实表述（实际上没有联网）。", "我没有联网或数据库回执，不能声称查过公开数据库；只能根据当前材料进行初步分析。"),
]

def main():
    rng = random.Random(SEED)
    rows = []
    wrappers = ["", "请准确回答：", "按要求作答：", "不要补充未验证的事实："]
    for _ in range(8):
        for q, a in CRITICAL:
            w = rng.choice(wrappers)
            rows.append({"prompt": w + q, "completion": a})
    base = [json.loads(x) for x in BASE.read_text().splitlines() if x.strip()]
    rng.shuffle(base)
    rows.extend({"prompt": x["prompt"], "completion": x["completion"]} for x in base[:96])
    rng.shuffle(rows)
    n = len(rows); ntr = int(n * .8); nv = int(n * .1)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, subset in (("train", rows[:ntr]), ("valid", rows[ntr:ntr+nv]), ("test", rows[ntr+nv:])):
        (OUT / f"{name}.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in subset) + "\n")
    print(json.dumps({"seed": SEED, "total": n, "train": ntr, "valid": nv, "test": n-ntr-nv}, ensure_ascii=False))

if __name__ == "__main__": main()
