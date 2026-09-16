"""Focused SSRF completeness repair with compact, evidence-safe answers."""
import json, random
from pathlib import Path
OUT=Path('/Users/jiehan/datasets/cybersec-phase23-ssrf'); SEED=20260924
SYSTEM='你是本地网安特化分析模块。涉及具体漏洞、CVE、KB、当前环境或外部检索时，只依据已提供的证据；没有证据就明确说无法核验并停止。普通知识问题可以直接回答，但不得声称使用了未连接的工具或来源。'
ROWS=[
 ('评审服务端 URL 抓取接口：只允许 HTTPS、拦截 127.0.0.1、禁止 Host 头。用六句话以内给出 SSRF 校验顺序。','先解析 URL 并限制协议与端口，再解析域名得到的每个 IPv4/IPv6 地址并拒绝回环、私网、链路本地和保留地址。连接前后都校验实际目标 IP，防止 DNS 重绑定；每次重定向都重新解析并重复检查。不要依赖字符串匹配或可伪造的 Host 头，并限制超时、响应大小和重定向次数。'),
 ('只允许 HTTPS、拦截 127.0.0.1 的 URL 抓取接口有哪些 SSRF 绕过面？','关键绕过包括 DNS rebinding、重定向到内网、IPv6 的 ::1 或 IPv4-mapped 地址、整数/八进制 IP 表示，以及只检查 URL 字符串而不检查实际连接 IP。防御应在解析后校验所有地址，连接时绑定已校验 IP，并对每次重定向重复解析和私网检查。'),
 ('禁止 Host 头能否单独防止 SSRF？为什么？','不能。Host 头限制不等于目标地址校验；攻击者仍可能利用 DNS rebinding、重定向、IPv6 或代理解析差异到达内网。应以解析后的实际 IP 做回环、私网、链路本地和保留地址检查，并在每跳重定向时重复执行。'),
 ('解释缓存为什么能减少重复计算，用两句话。','缓存保存已经计算过的结果，后续相同请求可以直接复用。这样能减少重复计算并降低响应延迟。'),
]
def main():
 r=random.Random(SEED); rows=[]
 for _ in range(30):
  for q,a in ROWS: rows.append({'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':q},{'role':'assistant','content':a}]})
 r.shuffle(rows); n=len(rows); a=12; b=12; OUT.mkdir(parents=True,exist_ok=True)
 for name,part in [('train',rows[:n-a-b]),('valid',rows[n-a-b:n-b]),('test',rows[n-b:])]: (OUT/f'{name}.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in part)+'\n')
 print(json.dumps({'seed':SEED,'total':n,'train':n-a-b,'valid':a,'test':b}))
if __name__=='__main__': main()
