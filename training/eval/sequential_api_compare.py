#!/usr/bin/env python3
"""串行比较生产与候选 API，避免本地推理锁造成假失败。"""
import argparse, json, pathlib, urllib.request

DEFAULT_CASES = [
    "法国的首都是哪里？",
    "解释什么是数据库索引。",
    "CSRF 的原理、检测和修复方法是什么？",
    "SSRF 防御为什么要校验解析后的 IP？",
    "没有工具回执时能否声称读取过文件？",
]

def ask(url, token, question, max_tokens):
    body = json.dumps({"model": "qwen-cyber-agent", "messages": [{"role": "user", "content": question}], "temperature": 0, "max_tokens": max_tokens}, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=body, headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    obj = json.load(urllib.request.urlopen(req, timeout=120))
    return (obj.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--production", default="http://127.0.0.1:18765/v1/chat/completions")
    ap.add_argument("--candidate", default="http://127.0.0.1:18766/v1/chat/completions")
    ap.add_argument("--token-file", default="~/.config/cyber-agent/api-token")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    token = pathlib.Path(args.token_file).expanduser().read_text().strip()
    rows = []
    for q in DEFAULT_CASES:
        p = ask(args.production, token, q, 220)
        c = ask(args.candidate, token, q, 220)
        rows.append({"question": q, "production": p, "candidate": c, "production_nonempty": bool(p.strip()), "candidate_nonempty": bool(c.strip())})
    pathlib.Path(args.output).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    print(f"production={sum(r['production_nonempty'] for r in rows)}/{len(rows)} candidate={sum(r['candidate_nonempty'] for r in rows)}/{len(rows)}")

if __name__ == "__main__":
    main()
