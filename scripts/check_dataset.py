#!/usr/bin/env python3
"""CI validator for cybersec-qa-dataset-zh.

Turns the manual quality bar into a machine-checkable gate. Exit 0 = clean,
1 = problems found. Run locally with: python3 scripts/check_dataset.py
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_ANSWER_CHARS = 150
TEMPLATE = re.compile(r"常见安全问题\d+")

# Purity rules: nation-state attribution / named groups / geopolitics must not
# appear. Patterns are precise to avoid flagging generic technical terms
# (e.g. "APT 攻击" the category, "CIA 三元组", "MSSQL").
DIRTY_PATTERNS = [
    r"APT\s*\d+",
    r"(俄罗斯|朝鲜|伊朗|以色列|北约)\s*(黑客|情报|网络攻击|组织|间谍|威胁行为者)",
    r"(中国|美国)\s*(黑客组织|间谍|情报机构|网络部队)",
    r"(国家支持|国家赞助|国家级攻击|nation[\-\s]state\s+actor)",
    r"\bFSB\b|\bGRU\b|\bUnit\s*61398\b|\bLazarus\s*Group\b",
    r"(NSA|CIA)\s*(黑客|武器库|攻击工具|泄露武器|归因)",
    r"(地缘政治|geopolit)",
    r"(Mandiant|CrowdStrike|FireEye)\s*(归因|attributed|report)",
]
DIRTY_RE = [re.compile(p, re.IGNORECASE) for p in DIRTY_PATTERNS]


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "batch*.jsonl")))
    if not files:
        print("ERROR: no batch*.jsonl files found")
        return 1

    problems = []
    total = 0
    seen_q = {}
    for f in files:
        rel = os.path.relpath(f, ROOT)
        for ln, line in enumerate(open(f, encoding="utf-8"), 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                o = json.loads(line)
            except Exception as e:
                problems.append(f"{rel}:{ln} invalid JSON ({e})")
                continue
            if set(o.keys()) != {"user", "assistant"}:
                problems.append(f"{rel}:{ln} bad schema, keys={sorted(o.keys())}")
            q = str(o.get("user", "")).strip()
            a = str(o.get("assistant", "")).strip()
            if not q or not a:
                problems.append(f"{rel}:{ln} empty user/assistant")
                continue
            if len(a) < MIN_ANSWER_CHARS:
                problems.append(f"{rel}:{ln} answer too short ({len(a)} chars)")
            if TEMPLATE.search(q):
                problems.append(f"{rel}:{ln} templated filler question")
            if q in seen_q:
                problems.append(f"{rel}:{ln} duplicate question (first at {seen_q[q]})")
            else:
                seen_q[q] = f"{rel}:{ln}"
            blob = q + " " + a
            for r in DIRTY_RE:
                m = r.search(blob)
                if m:
                    problems.append(f"{rel}:{ln} purity violation: {m.group()!r}")

    print(f"checked {total} records across {len(files)} files")
    if problems:
        print(f"\nFAIL — {len(problems)} issue(s):")
        for p in problems[:50]:
            print(f"  - {p}")
        if len(problems) > 50:
            print(f"  … and {len(problems) - 50} more")
        return 1
    print("PASS — valid JSON, uniform schema, no duplicates, no filler, purity clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
