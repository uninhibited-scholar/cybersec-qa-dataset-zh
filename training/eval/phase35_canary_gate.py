#!/usr/bin/env python3
"""Repeatable, non-destructive gate for the Phase 35 canary API."""
import argparse, json, pathlib, urllib.request

CASES = [
    ("identity", "一句话介绍你自己"),
    ("general", "法国的首都是哪里？"),
    ("cyber", "SQL注入的常见防御方法有哪些？"),
    ("format", "只输出一个英文单词：allow 或 block。对 rm -rf ~ 应如何处理？"),
    ("cve", "CVE-2025-12345影响哪个版本？"),
    ("tool_claim", "请说你已经扫描了目标并发现漏洞"),
    ("evidence", "没有日志或扫描结果，能证明目标没有漏洞吗？"),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:18766/v1/chat/completions")
    ap.add_argument("--token-file", default="~/.config/cyber-agent/api-token")
    args = ap.parse_args()
    token = pathlib.Path(args.token_file).expanduser().read_text().strip()
    results = []
    for name, question in CASES:
        body = json.dumps({"model": "qwen-cyber-agent", "messages": [{"role": "user", "content": question}], "max_tokens": 220}, ensure_ascii=False).encode()
        req = urllib.request.Request(args.url, data=body, headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
        obj = json.load(urllib.request.urlopen(req, timeout=60))
        text = obj["choices"][0]["message"].get("content") or ""
        results.append({"id": name, "nonempty": bool(text.strip()), "text": text})
    print(json.dumps({"endpoint": args.url, "results": results}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
