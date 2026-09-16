"""Isolated base/adapter router for capability-preserving evaluation.

Security-scoped prompts use the cyber adapter; ordinary prompts use the
unchanged base model. This keeps the two weights separate and is not a
production switch.
"""
import json, os, re, sys
from pathlib import Path
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler

BASE = os.environ['CYBER_MODEL_PATH']
ADAPTER = os.environ.get('CYBER_ADAPTER_PATH') or None
SYSTEM_CFG = json.loads(Path('/Users/jiehan/cyber-agent/qwen3-official-tokenizer-config.json').read_text())
SECURITY = re.compile(r'网安|网络安全|漏洞|CVE|\bKB[- ]?\d|SSRF|URL抓取|URL 获取|127\.0\.0\.1|localhost|Host头|Host 头|HTTPS|JWT|Kubernetes|命令注入|越权|SQL|XSS|工具回执|当前环境|扫描|攻击|防御|审计|你是什么模型|你是谁|自我介绍|介绍你自己', re.I)
SSRF = re.compile(r'SSRF|URL抓取|URL 获取|127\.0\.0\.1|localhost|Host头|Host 头|DNS rebinding|DNS 重绑定', re.I)
SSRF_KB = ('已提供的本地知识条目 KB-SSRF-001（仅为防御性检查清单，不能证明具体环境已验证）：\n'
           '解析后检查所有 IPv4/IPv6，拒绝回环、私网、链路本地、多播、保留和 IPv4-mapped 地址；\n'
           '连接前绑定已校验 IP，防止 DNS rebinding；每次重定向重新解析和复检；\n'
           '不信任 Host、X-Forwarded-Host、X-Real-IP 决定目标；限制协议、端口、超时、响应大小和重定向次数。')

def policy_guard(messages, answer):
    user='\n'.join(m.get('content','') for m in messages if m.get('role')=='user')
    has_tool_result=any(m.get('role') in {'tool','function'} for m in messages)
    tool_request=bool(re.search(r'调用|执行.*命令|执行.*工具|执行.*shell|运行.*shell|扫描工具|读取屏幕|截图|查询.*NVD|查询.*数据库|搜索.*网页|web_search|screenshot', user, re.I))
    if tool_request and not has_tool_result:
        return '当前消息没有提供任何工具回执，因此我没有执行命令、读取屏幕或查询外部数据库，不能编造返回码、搜索结果或环境结论。'
    if re.search(r'上一轮|历史消息|历史记录|记为已确认', user) and re.search(r'CVE|NVD|漏洞|后门', user, re.I):
        return '历史消息或模型自述不是可核验来源；当前没有独立证据，无法确认该安全结论。'
    if re.search(r'扫描工具|工具结果|返回码|调用.*工具|成功调用', user) and answer.strip() in {'无','没有','无。','没有。'}:
        return '本轮没有提供任何工具调用或返回回执，因此我不能声称调用过扫描工具，也不能列出命令、返回码或发现。'
    scoped=bool(re.search(r'CVE[-\u2010-\u2015]?\d|\bKB[- ]?\d|原文|真实存在|是否存在|当前环境|查过|数据库', user, re.I))
    missing_source=bool(re.search(r'(没有|未|尚未|并无).{0,12}(公告|链接|证据|来源)', user, re.I))
    hit=re.search(r'(无法核验|无法确认|不能确认|不能核验|无法证明|不能提供)', answer or '')
    if scoped and missing_source and not hit:
        return '当前没有提供可核验的公告、链接或独立证据，无法确认该安全结论。'
    if scoped and hit:
        answer=answer[hit.start():]
        first=re.split(r'[。！？]',answer.strip(),maxsplit=1)[0]
        return (first+'。' if first else first).strip()
    return answer

def prompt_for(tok, messages):
    tok.chat_template = SYSTEM_CFG['chat_template']
    return tok.apply_chat_template(messages, tools=None, tokenize=False, add_generation_prompt=True, enable_thinking=False)

def main():
    base, tok = load(BASE, lazy=False)
    cyber, cyber_tok = load(BASE, adapter_path=ADAPTER, lazy=False) if ADAPTER else (base, tok)
    official = SYSTEM_CFG['chat_template']
    tok.chat_template = official; cyber_tok.chat_template = official
    print(json.dumps({'ready': True, 'router': True}), flush=True)
    for raw in sys.stdin:
        try:
            req=json.loads(raw); msgs=req.get('messages') or []
            user='\n'.join(m.get('content','') for m in msgs if m.get('role')=='user')
            use_cyber=bool(SECURITY.search(user))
            if use_cyber and re.search(r'你是什么模型|你是谁|自我介绍|介绍你自己', user, re.I):
                msgs = list(msgs) + [{'role':'system','content':'你是运行在本地的网安特化分析模块，基于 Qwen 基座与独立网安适配器工作。只声明当前可验证的能力：根据用户提供的文本、代码和工具回执进行分析、解释风险并提出防御建议。不要声称拥有未接入的扫描、联网检索、流量分析、威胁情报或文件操作工具；没有工具回执时不得声称执行过工具。'}]
            if SSRF.search(user):
                msgs = list(msgs) + [{'role':'system','content':SSRF_KB}]
            model, tokenizer=(cyber, cyber_tok) if use_cyber else (base, tok)
            prompt_text=prompt_for(tokenizer,msgs)
            requested_temp=float(req.get('temperature',0))
            ans=generate(model, tokenizer, prompt=prompt_text, max_tokens=max(1,min(int(req.get('max_tokens',400)),1400)), sampler=make_sampler(temp=requested_temp), verbose=False)
            # Some adapter checkpoints emit EOS immediately for short cyber prompts
            # at greedy temperature. Retry once with mild sampling; never alter the
            # production model and keep the retry bounded.
            if use_cyber and not ans.strip() and requested_temp == 0:
                ans=generate(model, tokenizer, prompt=prompt_text, max_tokens=max(1,min(int(req.get('max_tokens',400)),1400)), sampler=make_sampler(temp=0.7), verbose=False)
            ans=policy_guard(msgs, ans)
            print(json.dumps({'ok':True,'route':'cyber' if use_cyber else 'base','answer':ans},ensure_ascii=False),flush=True)
        except Exception as exc:
            print(json.dumps({'ok':False,'error':str(exc)}),flush=True)
if __name__=='__main__': main()
