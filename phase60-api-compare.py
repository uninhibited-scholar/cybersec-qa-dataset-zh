#!/usr/bin/env python3
import json, os, sys, time, urllib.request

def call(url, token, q):
    body=json.dumps({'model':'qwen-cyber-agent','messages':[{'role':'user','content':q}],'max_tokens':220},ensure_ascii=False).encode()
    req=urllib.request.Request(url,data=body,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    obj=json.load(urllib.request.urlopen(req,timeout=90)); return obj['choices'][0]['message'].get('content') or ''

def main():
    if len(sys.argv)!=4: raise SystemExit('usage: compare.py questions.jsonl prod_url cand_url')
    qs=[json.loads(x)['question'] for x in open(sys.argv[1],encoding='utf-8') if x.strip()][:14]
    tok=open(os.path.expanduser('~/.config/cyber-agent/api-token')).read().strip(); rows=[]
    for i,q in enumerate(qs,1):
        row={'id':i,'question':q}
        for name,url in [('production',sys.argv[2]),('candidate',sys.argv[3])]:
            try: t=call(url,tok,q); row[name]={'nonempty':bool(t.strip()),'text':t}
            except Exception as e: row[name]={'nonempty':False,'error':type(e).__name__+': '+str(e)}
        rows.append(row); print(f'{i}/{len(qs)}',flush=True)
    print(json.dumps({'total':len(rows),'production_nonempty':sum(r['production']['nonempty'] for r in rows),'candidate_nonempty':sum(r['candidate']['nonempty'] for r in rows),'rows':rows},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
