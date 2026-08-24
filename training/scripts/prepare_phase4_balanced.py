#!/usr/bin/env python3
"""Build a deterministic phase-4 mixture without copying private data into Git."""

import argparse
import hashlib
import json
import random
from pathlib import Path

IDENTITY = (
    "你是运行在用户 Mac mini 上、通过 API 接入 Agent Harness 的本地网安特化模型。"
    "优先给出具体的原理、证据、检测、风险判断、修复与验证步骤。"
    "不得虚构工具调用、CVE、知识库编号、项目审计结果或安全结论；证据不足时明确标注未知。"
)


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def normalize_clean(row):
    prompt = row["prompt"]
    marker = "\n问题："
    question = prompt.split(marker, 1)[1].rsplit("\n回答：", 1)[0] if marker in prompt else prompt
    return {
        "prompt": f"{IDENTITY}\n问题：{question.strip()}\n回答：",
        "completion": row["completion"].strip(),
    }


def fingerprint(row):
    data = (row["prompt"] + "\0" + row["completion"]).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sample(rows, count, seed):
    rows = list(rows)
    random.Random(seed).shuffle(rows)
    if len(rows) < count:
        raise ValueError(f"need {count} rows, found {len(rows)}")
    return rows[:count]


def write_split(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", type=Path, required=True)
    parser.add_argument("--grounded", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260824)
    args = parser.parse_args()

    plan = {
        "train": (2700, 900),
        "valid": (300, 100),
        "test": (350, 150),
    }
    seen = set()
    manifest = {"seed": args.seed, "splits": {}}

    for index, (split, (clean_n, grounded_n)) in enumerate(plan.items()):
        clean_rows = (normalize_clean(r) for r in read_jsonl(args.clean / f"{split}.jsonl"))
        grounded_rows = read_jsonl(args.grounded / f"{split}.jsonl")
        chosen = sample(clean_rows, clean_n, args.seed + index * 2)
        chosen += sample(grounded_rows, grounded_n, args.seed + index * 2 + 1)
        unique = []
        for row in chosen:
            key = fingerprint(row)
            if key not in seen:
                seen.add(key)
                unique.append(row)
        random.Random(args.seed + 100 + index).shuffle(unique)
        write_split(args.output / f"{split}.jsonl", unique)
        manifest["splits"][split] = {
            "requested_clean": clean_n,
            "requested_grounded": grounded_n,
            "written": len(unique),
            "sha256": hashlib.sha256((args.output / f"{split}.jsonl").read_bytes()).hexdigest(),
        }

    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
