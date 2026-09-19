"""Audit nominal case count versus normalized prompt-core diversity."""
import argparse
from collections import defaultdict
import hashlib
import json
import re
from pathlib import Path

WRAPPERS = re.compile(
    r"^(请按代码审查报告结构回答（问题、证据、修复、验证）：|"
    r"从检测、修复、验证三个阶段回答：|"
    r"以授权防守评估为前提，做威胁建模：)"
)
NUMBERED = re.compile(r"^(工具诚实性案例|提示注入案例|多轮案例|格式案例|案例)\d+：")


def core(prompt):
    prompt = WRAPPERS.sub("", prompt)
    return NUMBERED.sub("", prompt).strip()


def audit(path):
    raw = path.read_bytes()
    cases = json.loads(raw)
    groups = defaultdict(list)
    by_category = defaultdict(lambda: {"rows": 0, "unique_cores": 0})
    ids = set()
    for case in cases:
        ids.add(case["id"])
        groups[core(case["prompt"])].append(case["id"])
        by_category[case["category"]]["rows"] += 1
    for case in cases:
        by_category[case["category"]]["unique_cores"] = len({
            core(row["prompt"]) for row in cases if row["category"] == case["category"]
        })
    multiturn_sequences = {
        "\n".join(message["content"] for message in case.get("messages", []) if message.get("role") == "user").strip()
        for case in cases if case.get("category") == "multiturn"
    }
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "rows": len(cases),
        "unique_ids": len(ids),
        "unique_exact_prompts": len({c["prompt"] for c in cases}),
        "unique_normalized_cores": len(groups),
        "largest_duplicate_core_group": max(map(len, groups.values())),
        "category_counts": dict(sorted(by_category.items())),
        "structured_multiturn_cases": sum(
            case.get("category") == "multiturn"
            and [m.get("role") for m in case.get("messages", [])] == ["user", "assistant", "user"]
            for case in cases
        ),
        "unique_multiturn_user_sequences": len(multiturn_sequences),
        "invalid_multiturn_cases": [
            case.get("id") for case in cases
            if case.get("category") == "multiturn"
            and [m.get("role") for m in case.get("messages", [])] != ["user", "assistant", "user"]
        ],
        "duplicate_core_groups": sum(len(v) > 1 for v in groups.values()),
        "note": "Normalization removes only known category wrappers and case-number prefixes; it is a targeted audit, not a general semantic-similarity proof.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.manifest)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered)
