import json, pathlib
root=pathlib.Path(__file__).parent
required={"train":7,"valid":1,"test":1}
for name,n in required.items():
 p=root/f"phase81_{name}.jsonl"; rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
 assert len(rows)==n, (name,len(rows))
 for r in rows:
  assert isinstance(r.get('messages'),list) and len(r['messages'])==2
  assert [m['role'] for m in r['messages']]==['user','assistant']
  assert all(isinstance(m.get('content'),str) and m['content'].strip() for m in r['messages'])
  text=' '.join(m['content'] for m in r['messages']).lower()
  assert not any(x in text for x in ['bank','银行日志','secret_marker','password=','token=','rm -rf'])
print('phase81 dataset audit passed: 7/1/1; no private markers, payloads, or template residue')
