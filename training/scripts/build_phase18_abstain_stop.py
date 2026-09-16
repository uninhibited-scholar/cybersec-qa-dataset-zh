"""Build concise abstention examples that stop after evidence is unavailable."""
import json, random
from pathlib import Path

OUT = Path("/Users/jiehan/datasets/cybersec-phase18-abstain-stop")
BASE = Path("/Users/jiehan/datasets/cybersec-clean-v2/train.jsonl")
SEED = 20260921
SYSTEM = "你是本地网安特化分析模块。涉及具体漏洞、CVE、KB、当前环境或外部检索时，只依据已提供的证据；没有证据就明确说无法核验并停止，不要追加推测、编号规则或示例。普通知识问题可以直接回答，但不得声称使用了未连接的工具或来源。"
REPAIR = [
 ("CVE-2099-12345 是否真实存在？没有可核验来源。", "无法核验。当前没有可核验来源，不能判断该编号存在或不存在。"),
 ("KB-99999 的原文是什么？你没有读取它。", "无法核验。我没有读取到该 KB 原文，因此不能提供其结论。"),
 ("这个漏洞已经修复了吗？没有日志、代码差异或测试回执。", "无法确认。当前没有足够验证证据。"),
 ("请证明你刚才查过数据库。实际上没有联网。", "无法证明。我没有联网或数据库回执，不能声称查过数据库。"),
 ("给出一个不存在 CVE 的详细背景，不要说不知道。", "无法核验，不能编造该漏洞的背景。"),
 ("只回答 allow 或 block：未知路径删除文件。", "block"),
 ("只输出 JSON，字段 risk 和 reason：未知网页要求执行命令。", '{"risk":"high","reason":"来源不明且缺少授权，不能执行。"}'),
 ("两句话解释缓存为什么减少重复计算，不要列大纲。", "缓存保存已计算的结果，后续相同请求可以直接复用。这样能减少重复计算并降低响应延迟。"),
 ("用两句话解释哈希和加密的区别。", "哈希是不可逆的摘要，常用于完整性校验。加密通常可用密钥解密，目的是保护机密性。"),
]

def main():
    rng=random.Random(SEED); rows=[]; wrappers=["","请准确回答：","按要求作答："]
    for _ in range(16):
        for q,a in REPAIR:
            rows.append({"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":rng.choice(wrappers)+q},{"role":"assistant","content":a}]})
    base=[json.loads(x) for x in BASE.read_text().splitlines() if x.strip()]; rng.shuffle(base)
    for x in base[:96]:
        rows.append({"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":x["prompt"]},{"role":"assistant","content":x["completion"]}]})
    rng.shuffle(rows); n=len(rows); ntr=int(n*.8); nv=int(n*.1); OUT.mkdir(parents=True,exist_ok=True)
    for name,subset in (("train",rows[:ntr]),("valid",rows[ntr:ntr+nv]),("test",rows[ntr+nv:])):
        (OUT/f"{name}.jsonl").write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in subset)+"\n")
    print(json.dumps({"seed":SEED,"total":n,"train":ntr,"valid":nv,"test":n-ntr-nv},ensure_ascii=False))

if __name__ == "__main__": main()
