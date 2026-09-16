from pathlib import Path
p=Path('/Users/jiehan/cyber-agent/chat_worker_v2.py')
s=p.read_text()
s=s.replace('first = re.split(r"(?:\\r?\\n){2,}|\\r?\\n|(?<=[。！？])\\s+", answer.strip(), maxsplit=1)[0]\n    return first.strip()', 'first = re.split(r"[。！？]", answer.strip(), maxsplit=1)[0]\n    return (first + "。" if first else first).strip()')
p.write_text(s)
