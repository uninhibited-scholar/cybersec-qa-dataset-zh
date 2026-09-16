"""Run the isolated worker policy cases against a remote Mac mini candidate."""
import json, subprocess
from pathlib import Path

CASES = Path(__file__).with_name('phase30-worker-policy-cases.json')
REMOTE = 'jiehan@100.83.34.62'
WORKER = '/Users/jiehan/cyber-agent/chat_worker_router.py'
PYTHON = '/Users/jiehan/venvs/agents-a1/bin/python'
MODEL = '/Users/jiehan/models/Qwen3-4B-official-chatml-phase10'

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--adapter', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    cases = json.loads(CASES.read_text())
    requests = []
    for c in cases:
        msgs = [{'role': 'user', 'content': c['prompt']}]
        if c.get('tool_result'):
            msgs.append({'role': 'tool', 'content': c['tool_result']})
        requests.append({'id': c['id'], 'messages': msgs, 'max_tokens': 120, 'temperature': 0})
    remote_cmd = f'CYBER_MODEL_PATH={MODEL} CYBER_ADAPTER_PATH={args.adapter} {PYTHON} {WORKER}'
    p = subprocess.run(['ssh', REMOTE, remote_cmd], input=''.join(json.dumps(x, ensure_ascii=False)+'\n' for x in requests), text=True, capture_output=True, check=True)
    rows = [json.loads(line) for line in p.stdout.splitlines() if line.startswith('{')]
    rows = [x for x in rows if x.get('ok') is True]
    result = {'candidate': args.adapter, 'cases': len(cases), 'responses': rows, 'production_changed': False}
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'cases': len(cases), 'responses': len(rows), 'output': args.output}, ensure_ascii=False))

if __name__ == '__main__':
    main()
