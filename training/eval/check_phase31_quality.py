"""Quality gate for candidate responses; does not judge technical correctness."""
import json, re, sys

data = json.load(open(sys.argv[1], encoding='utf-8'))
rows = data['responses']
checks = []
for row in rows:
    answer = row.get('answer', '').strip()
    # Flag accidental long English runs in Chinese short-answer cases.
    # Structured outputs intentionally contain English field names/labels.
    structured = answer in {'allow', 'block', 'yes', 'no'} or answer.startswith('{')
    latin_runs = [] if structured else re.findall(r'[A-Za-z]{8,}', answer)
    checks.append({
        'route': row.get('route'),
        'nonempty': bool(answer),
        'long_latin_runs': latin_runs,
        'quality_pass': bool(answer) and not latin_runs,
    })
print(json.dumps({'cases': len(checks), 'quality_pass': sum(x['quality_pass'] for x in checks), 'checks': checks}, ensure_ascii=False, indent=2))
