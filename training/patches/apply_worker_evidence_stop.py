from pathlib import Path
p = Path('/Users/jiehan/cyber-agent/chat_worker_v2.py')
s = p.read_text()
s = s.replace('import os\nimport sys', 'import os\nimport re\nimport sys')
needle = "    return tokenizer.apply_chat_template(messages, tools=tools or None,\n        tokenize=False, add_generation_prompt=True, enable_thinking=False)\n"
insert = needle + '''\ndef enforce_evidence_stop(messages, answer):\n    """Stop unsupported elaboration after a terminal abstention."""\n    user_text = "\\n".join(m.get("content", "") for m in messages if m.get("role") == "user")\n    scoped = bool(re.search(r"CVE[-\\u2010-\\u2015]?\\d|\\bKB[- ]?\\d|原文|真实存在|是否存在|当前环境|查过|数据库", user_text, re.I))\n    abstain = bool(re.match(r"\\s*(无法核验|无法确认|不能确认|不能核验|无法证明|不能提供)", answer or ""))\n    if not (scoped and abstain):\n        return answer\n    first = re.split(r"(?:\\r?\\n){2,}|\\r?\\n|(?<=[。！？])\\s+", answer.strip(), maxsplit=1)[0]\n    return first.strip()\n'''
if 'def enforce_evidence_stop' not in s:
    s = s.replace(needle, insert)
old = "                sampler=make_sampler(temp=float(req.get('temperature', 0))), verbose=False)\n            result = {'ok': True, 'answer': answer}"
new = "                sampler=make_sampler(temp=float(req.get('temperature', 0))), verbose=False)\n            answer = enforce_evidence_stop(req.get('messages') or [], answer)\n            result = {'ok': True, 'answer': answer}"
if old not in s:
    raise SystemExit('generation anchor missing')
p.write_text(s.replace(old, new))
