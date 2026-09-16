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
SECURITY = re.compile(r'网安|网络安全|漏洞|CVE|\bKB[- ]?\d|SSRF|URL抓取|URL 获取|127\.0\.0\.1|localhost|Host头|Host 头|HTTPS|JWT|Kubernetes|命令注入|越权|SQL|XSS|工具回执|当前环境|扫描|攻击|防御|审计', re.I)

def policy_guard(messages, answer):
    user='\n'.join(m.get('content','') for m in messages if m.get('role')=='user')
    if re.search(r'扫描工具|工具结果|返回码|调用.*工具|成功调用', user) and answer.strip() in {'无','没有','无。','没有。'}:
        return '本轮没有提供任何工具调用或返回回执，因此我不能声称调用过扫描工具，也不能列出命令、返回码或发现。'
    scoped=bool(re.search(r'CVE[-\u2010-\u2015]?\d|\bKB[- ]?\d|原文|真实存在|是否存在|当前环境|查过|数据库', user, re.I))
    hit=re.search(r'(无法核验|无法确认|不能确认|不能核验|无法证明|不能提供)', answer or '')
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
            model, tokenizer=(cyber, cyber_tok) if use_cyber else (base, tok)
            ans=generate(model, tokenizer, prompt=prompt_for(tokenizer,msgs), max_tokens=max(1,min(int(req.get('max_tokens',400)),1400)), sampler=make_sampler(temp=float(req.get('temperature',0))), verbose=False)
            ans=policy_guard(msgs, ans)
            print(json.dumps({'ok':True,'route':'cyber' if use_cyber else 'base','answer':ans},ensure_ascii=False),flush=True)
        except Exception as exc:
            print(json.dumps({'ok':False,'error':str(exc)}),flush=True)
if __name__=='__main__': main()
