"""Authenticated API smoke runner; token must be supplied via environment."""
import json, os, urllib.request

def main():
    token = os.environ.get('CYBER_API_TOKEN')
    if not token:
        raise SystemExit('CYBER_API_TOKEN is not set; refusing to guess or read credentials.')
    url = os.environ.get('CYBER_API_URL', 'http://127.0.0.1:18766/v1/chat/completions')
    body = {'messages': [{'role': 'user', 'content': '一句话说明 SQL 注入的主要风险。'}], 'max_tokens': 120, 'temperature': 0}
    req = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode(), headers={'Content-Type':'application/json', 'Authorization':'Bearer '+token})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    print(json.dumps({'status':'ok', 'has_answer': bool(data.get('choices', [{}])[0].get('message', {}).get('content', '').strip())}, ensure_ascii=False))

if __name__ == '__main__': main()
