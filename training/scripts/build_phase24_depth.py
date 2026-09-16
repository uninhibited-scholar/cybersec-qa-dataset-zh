"""Curated professional-depth repair for the cyber adapter."""
import json, random
from pathlib import Path
OUT=Path('/Users/jiehan/datasets/cybersec-phase24-depth'); SEED=20260925
SYSTEM='你是本地网安特化分析模块。涉及具体漏洞、CVE、KB、当前环境或外部检索时，只依据已提供的证据；没有证据就明确说无法核验并停止。普通知识问题可以直接回答，但不得声称使用了未连接的工具或来源。'
ROWS=[
('SSRF 校验顺序是什么？','先解析 URL 与端口，再解析所有 IPv4/IPv6 地址并拒绝回环、私网、链路本地和保留地址。连接时绑定已校验 IP；每次重定向重新解析和检查，防止 DNS rebinding。不要只做字符串匹配，也不要信任可伪造的 Host 头。'),
('HTTPS、127.0.0.1 和 Host 头限制为什么仍可能被 SSRF 绕过？','攻击者可能利用 DNS rebinding、重定向、IPv6 的 ::1、IPv4-mapped 地址或整数 IP 表示。防御应检查解析后的实际 IP，并在连接前后和每次重定向重复验证。'),
('RS256 与 HS256 同时启用的算法混淆风险是什么？','服务端必须按 issuer 或端点固定允许的 alg，并将 RS256 绑定公钥、HS256 绑定独立共享密钥，拒绝算法回退。验证 issuer、audience、exp、nbf 和签名后再建立身份。不能把 RSA 公钥当作 HMAC secret。'),
('JWT 算法混淆的回归测试要点？','测试修改 alg、使用错误密钥类型、缺失 issuer/audience、过期 token 和签名篡改；每个 issuer 只接受白名单算法，并确认失败时不建立会话。'),
('hostPath 与 privileged Pod 的风险和修复？','hostPath 可读写节点文件，privileged 扩大设备和内核能力；两者叠加可能导致节点级影响。用 Pod Security Admission 或等效准入策略拒绝 privileged、hostPath 和 host namespace，收紧 RBAC 并审计创建事件。'),
('Kubernetes 最小权限验证看什么？','检查 ServiceAccount、RBAC verbs/resources、hostNetwork/hostPID/hostIPC、Linux capabilities、allowPrivilegeEscalation、卷类型和准入审计；用拒绝用例验证策略确实生效。'),
('shell=True 拼接 filename 属于什么问题？如何修复？','这是命令注入，不是单纯路径遍历。不要拼接 shell 字符串，使用参数数组 shell=False，并对白名单路径做规范化；用包含分号、管道和命令替换的回归用例确认不会执行额外命令。'),
('归档路径遍历与命令注入有什么区别？','路径遍历发生在解压条目写出目录时，命令注入发生在 shell 解析用户输入时；两者证据和修复不同。解压时拒绝绝对路径与 .. 逃逸，执行命令时使用参数数组并关闭 shell。'),
('解释缓存为什么能减少重复计算，用两句话。','缓存保存已经计算过的结果，后续相同请求可以直接复用。这样能减少重复计算并降低响应延迟。'),
('没有工具回执时如何回答？','本轮没有提供工具调用或返回回执，因此不能声称执行过工具，也不能编造命令、返回码或发现。'),
]
def main():
 r=random.Random(SEED); rows=[]
 for _ in range(16):
  for q,a in ROWS: rows.append({'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':q},{'role':'assistant','content':a}]})
 r.shuffle(rows); n=len(rows); a=16; b=16; OUT.mkdir(parents=True,exist_ok=True)
 for name,part in [('train',rows[:n-a-b]),('valid',rows[n-a-b:n-b]),('test',rows[n-b:])]: (OUT/f'{name}.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in part)+'\n')
 print(json.dumps({'seed':SEED,'total':n,'train':n-a-b,'valid':a,'test':b}))
if __name__=='__main__': main()
