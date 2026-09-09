"""New ordinary-task holdout, not a domain benchmark. Never used for training."""
import json
import os
import subprocess
import time
from pathlib import Path

CASES = [
 ('sum','只输出整数。','17加26是多少？','43'),
 ('subtract','只输出整数。','50减18是多少？','32'),
 ('books','只输出整数。','四袋各8颗糖，总共吃掉5颗，还剩几颗？','27'),
 ('fraction','只输出整数。','80的四分之一是多少？','20'),
 ('json','只输出JSON对象，不要代码围栏。','把姓名小林、年龄24写为name和age两个字段。',None),
 ('label','只输出 pending、done 或 failed。','任务状态显示正在排队。', 'pending'),
 ('no_evidence','只输出 verified 或 unverified。没有一手证据时输出 unverified。','群聊称门票已退款，没有回执。','unverified'),
 ('evidence','只输出 verified 或 unverified。按题内明确提供的回执判断。','回执显示任务R8已成功完成。只判断该任务的回执状态。','verified'),
 ('translate','只输出译文。','把 Good morning 翻译成中文。',None),
 ('extract','只输出原文中的日期，格式YYYY-MM-DD。','研讨会定于2026-10-12，地点未定。','2026-10-12'),
 ('history','只回答用户当前问题，不补充其他内容。','我刚才说的代号是什么？','橙子'),
 ('explain','用一句话解释，不要列大纲。','缓存为什么能减少重复计算？',None),
]

root=Path('/Users/jiehan/cyber-agent')
out=root/('phase9-expanded-'+time.strftime('%Y%m%d-%H%M%S')+'.jsonl')
with out.open('x') as f:
 for label,adapter in [('base',''),('phase9','/Users/jiehan/models/phase9-fresh-chatml-20260909')]:
    env=dict(os.environ,CYBER_MODEL_PATH='/Users/jiehan/models/Qwen3-4B-mlx-4bit',CYBER_ADAPTER_PATH=adapter)
    proc=subprocess.Popen(['/Users/jiehan/venvs/agents-a1/bin/python','-u',str(root/'chat_worker_v2.py')],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    try:
        assert json.loads(proc.stdout.readline())['ready']
        for case,system,user,expected in CASES:
            messages=[dict(role='system',content=system)]
            if case=='history':
                messages += [dict(role='user',content='记住我的代号是橙子。'),dict(role='assistant',content='好的。')]
            messages.append(dict(role='user',content=user))
            proc.stdin.write(json.dumps(dict(messages=messages,max_tokens=100),ensure_ascii=False)+'\n');proc.stdin.flush()
            response=json.loads(proc.stdout.readline())
            answer=response.get('answer','').strip()
            passed=answer==expected if expected is not None else None
            if case=='json':
                try: passed=json.loads(answer)==dict(name='小林',age=24)
                except ValueError: passed=False
            row=dict(model=label,case=case,expected=expected,exact_pass=passed,**response)
            line=json.dumps(row,ensure_ascii=False);f.write(line+'\n');f.flush();print(line,flush=True)
    finally:
        proc.stdin.close();proc.wait(timeout=20)
print('Output:',out,flush=True)
