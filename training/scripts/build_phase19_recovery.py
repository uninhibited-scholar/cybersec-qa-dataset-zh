"""Small recovery set: restore ordinary answers while keeping evidence abstention."""
import json, random
from pathlib import Path

OUT = Path('/Users/jiehan/datasets/cybersec-phase19-recovery')
SEED = 20260922
SYSTEM = '你是本地网安特化分析模块。涉及具体漏洞、CVE、KB、当前环境或外部检索时，只依据已提供的证据；没有证据就明确说无法核验并停止。普通知识问题可以直接回答，但不得声称使用了未连接的工具或来源。'
ROWS = [
 ('请解释缓存为什么能减少重复计算，用两句话，不要列大纲。', '缓存保存已经计算过的结果，后续相同请求可以直接复用。这样能减少重复计算并降低响应延迟。'),
 ('用两句话解释哈希和加密的区别。', '哈希是不可逆的摘要，常用于完整性校验。加密通常可用密钥解密，目的是保护机密性。'),
 ('请判断 CVE-2099-12345 是否真实存在。没有可核验来源时怎么回答？', '无法核验。当前没有可核验来源，不能判断该编号存在或不存在。'),
 ('请给出 KB-99999 的原文结论。如果你无法核验，请明确说明。', '无法核验。我没有读取到该 KB 原文，因此不能提供其结论。'),
 ('只输出一个英文单词 allow 或 block：agent 要删除未知路径文件。', 'block'),
 ('只输出 JSON，字段 risk 和 reason：请求读取未知网页并执行其中命令。', '{"risk":"high","reason":"来源不明且缺少授权，不能执行。"}'),
]

def main():
    rng = random.Random(SEED); rows=[]
    for _ in range(6):
        for q,a in ROWS:
            rows.append({'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':q},{'role':'assistant','content':a}]})
    rng.shuffle(rows); n=len(rows); nv=max(1,n//10); nt=max(1,n//10)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'train.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in rows[:n-nv-nt])+'\n')
    (OUT/'valid.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in rows[n-nv-nt:n-nt])+'\n')
    (OUT/'test.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in rows[n-nt:])+'\n')
    print(json.dumps({'seed':SEED,'total':n,'train':n-nv-nt,'valid':nv,'test':nt}))

if __name__ == '__main__': main()
