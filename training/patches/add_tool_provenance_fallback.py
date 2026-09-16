from pathlib import Path
p=Path('/Users/jiehan/cyber-agent/chat_worker_v2.py')
s=p.read_text()
needle='''    if not (scoped and abstain):
        return answer
'''
replacement='''    provenance = bool(re.search(r"扫描工具|工具结果|返回码|调用.*工具|成功调用", user_text))
    if provenance and answer.strip() in {"无", "没有", "无。", "没有。"}:
        return "本轮没有提供任何工具调用或返回回执，因此我不能声称调用过扫描工具，也不能列出命令、返回码或发现。"
    if not (scoped and abstain):
        return answer
'''
if replacement not in s:
    if needle not in s: raise SystemExit('anchor missing')
    s=s.replace(needle,replacement,1)
p.write_text(s)
