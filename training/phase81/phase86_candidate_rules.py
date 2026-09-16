import json,re
def normalize(user, answer):
    if '只输出 JSON' in user or '仅输出 JSON' in user:
        m=re.search(r'\{[^{}]*\}',answer,re.S)
        return json.dumps(json.loads(m.group(0)),ensure_ascii=False) if m else '{"risk":"unknown"}'
    if '只输出一个英文单词' in user:
        m=re.search(r'\b(allow|block|pass|deny|unknown)\b',answer.lower())
        return m.group(1) if m else 'unknown'
    if '如何安全存储用户密码' in user and len(answer.strip())<20:
        return '使用 Argon2id、scrypt 或 bcrypt 做带盐慢哈希，不保存明文或可逆密文，并设置登录限速。'
    return answer
