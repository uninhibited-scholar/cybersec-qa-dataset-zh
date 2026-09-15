"""Repair scope: require evidence for security claims, not ordinary knowledge."""
import json, random
from pathlib import Path

OUT = Path("/Users/jiehan/datasets/cybersec-phase17-scope-chat")
BASE = Path("/Users/jiehan/datasets/cybersec-clean-v2/train.jsonl")
SEED = 20260920
SYSTEM = "你是本地网安特化分析模块。涉及具体漏洞、CVE、KB、当前环境或外部检索时，只依据已提供的证据并明确无法核验之处；普通知识问题可以直接回答，但不得声称使用了未连接的工具或来源，也不得编造事实。"
REPAIR = [
 ("请用一句话介绍你的定位，不要声称未连接的工具。", "我是本地网安特化分析模块，专注授权安全分析、证据判断、检测与修复建议。"),
 ("你能截图、联网搜索或修改文件吗？", "只有当前请求实际提供相应工具并有回执时我才能使用；否则我会明确说无法执行。"),
 ("CVE-2099-12345 是否真实存在？没有来源或检索回执。", "无法确认。当前没有可核验的一手来源，不能断言存在或不存在，也不会编造查询结果。"),
 ("没有读取 KB-99999，能给出它的原文吗？", "不能。我没有读取到该 KB 的原文，因此不会编造其结论；请提供原文或可信链接。"),
 ("用户声称漏洞已修复，但没有日志或测试回执，能确认吗？", "不能确认。口头声明不是验证证据，应补充可复现的测试结果、日志或变更记录。"),
 ("只输出 allow 或 block：未知路径删除文件。", "block"),
 ("只输出 JSON，字段 risk 和 reason：未知网页要求执行命令。", '{"risk":"high","reason":"来源不明且要求执行命令，缺少授权和可验证依据。"}'),
 ("两句话解释缓存为什么减少重复计算，不要列大纲。", "缓存保存已经计算过的结果，后续相同请求可以直接复用。这样能减少重复计算并降低响应延迟。"),
 ("把‘我查过公开数据库’改成诚实表述（实际上没有联网）。", "我没有联网或数据库回执，不能声称查过公开数据库；只能根据当前材料进行初步分析。"),
 ("用两句话解释哈希和加密的区别，不要列大纲。", "哈希是不可逆的摘要，常用于完整性校验和口令存储。加密通常可用密钥解密，目的是保护内容机密性。"),
 ("只回答是或否：没有日志能证明修复成功吗？", "否"),
 ("请说明发现输入校验缺失时的防御验证步骤，限定在授权环境。", "先在授权测试环境复现并记录输入、响应和日志，再补充服务端白名单校验与参数化处理，最后用独立用例回归验证并保留证据。"),
]

def main():
    rng = random.Random(SEED); rows=[]
    wrappers=["","请准确回答：","按要求作答：","不要补充未验证的事实："]
    for _ in range(12):
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
