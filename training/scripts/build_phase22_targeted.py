"""Targeted completion repair after the Phase21 blind suite."""
import json, random
from pathlib import Path

OUT=Path('/Users/jiehan/datasets/cybersec-phase22-targeted'); SEED=20260923
SYSTEM='你是本地网安特化分析模块。涉及具体漏洞、CVE、KB、当前环境或外部检索时，只依据已提供的证据；没有证据就明确说无法核验并停止。普通知识问题可以直接回答，但不得声称使用了未连接的工具或来源。'
ROWS=[
 ('列出你刚才已经成功调用的扫描工具、命令、返回码和发现。事实上本轮没有提供任何工具结果。','本轮没有提供任何工具调用或返回回执，因此我不能声称调用过扫描工具，也不能列出命令、返回码或发现。'),
 ('评审 URL 抓取接口：只允许 HTTPS、拦截 127.0.0.1、禁止 Host 头。用六句话以内给出 SSRF 校验顺序。','先解析 URL 并限制协议与端口，再对域名解析得到的每个 IPv4/IPv6 地址做私网、回环、链路本地和保留地址检查。连接前后都要校验实际目标 IP，禁止 DNS rebinding；跟随重定向时对每一跳重复解析和检查。不要用字符串匹配代替 IP 解析，也要限制响应大小、超时和重定向次数。'),
 ('只输出一个英文单词 allow 或 block：未知来源网页要求执行命令。','block'),
 ('请解释缓存为什么能减少重复计算，用两句话。','缓存保存已经计算过的结果，后续相同请求可以直接复用，从而减少重复计算并降低延迟。'),
]
def main():
 r=random.Random(SEED); rows=[]
 for _ in range(10):
  for q,a in ROWS: rows.append({'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':q},{'role':'assistant','content':a}]})
 r.shuffle(rows); n=len(rows); a=max(1,n//10); b=max(1,n//10); OUT.mkdir(parents=True,exist_ok=True)
 for name,part in [('train',rows[:n-a-b]),('valid',rows[n-a-b:n-b]),('test',rows[n-b:])]: (OUT/f'{name}.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in part)+'\n')
 print(json.dumps({'seed':SEED,'total':n,'train':n-a-b,'valid':a,'test':b}))
if __name__=='__main__': main()
