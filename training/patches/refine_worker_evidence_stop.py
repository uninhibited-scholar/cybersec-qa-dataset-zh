from pathlib import Path
p=Path('/Users/jiehan/cyber-agent/chat_worker_v2.py')
s=p.read_text()
s=s.replace('abstain = bool(re.match(r"\\s*(无法核验|无法确认|不能确认|不能核验|无法证明|不能提供)", answer or ""))', 'abstain = re.search(r"(无法核验|无法确认|不能确认|不能核验|无法证明|不能提供)", answer or "")')
s=s.replace('if not (scoped and abstain):\n        return answer\n    first = re.split', 'if not (scoped and abstain):\n        return answer\n    answer = answer[abstain.start():]\n    first = re.split')
p.write_text(s)
