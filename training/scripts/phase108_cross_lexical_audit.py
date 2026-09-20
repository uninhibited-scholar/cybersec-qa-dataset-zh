#!/usr/bin/env python3
"""Stream train-to-eval lexical overlap; output IDs/row numbers, never content."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata


def grams(text):
    text = re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", text).casefold())
    return {text[i:i+4] for i in range(max(0, len(text)-3))}


def audit(train, cases_path, threshold=0.3):
    cases = json.loads(cases_path.read_text())
    vectors = [grams("\n".join(m["content"] for m in case.get("messages", [])
                              if m.get("role") == "user") or case["prompt"]) for case in cases]
    index = defaultdict(list)
    for i, vector in enumerate(vectors):
        for gram in vector:
            index[gram].append(i)
    best = [{"case_id": case["id"], "jaccard": 0.0, "train_line": None} for case in cases]
    train_hash = hashlib.sha256()
    count = 0
    with train.open("rb") as stream:
        for lineno, raw in enumerate(stream, 1):
            train_hash.update(raw)
            if not raw.strip():
                continue
            row = json.loads(raw)
            text = row.get("prompt")
            if not isinstance(text, str):
                raise ValueError("Expected prompt/completion training data")
            vector = grams(text)
            count += 1
            intersections = Counter(i for gram in vector for i in index.get(gram, []))
            for i, intersection in intersections.items():
                similarity = intersection / (len(vector) + len(vectors[i]) - intersection)
                if similarity > best[i]["jaccard"]:
                    best[i].update(jaccard=similarity, train_line=lineno)
    flagged = [item for item in best if item["jaccard"] >= threshold]
    return {"method": "normalized character 4-gram set Jaccard, train prompts versus joined eval user turns",
            "threshold": threshold, "train_rows": count, "eval_cases": len(cases),
            "train_sha256": train_hash.hexdigest(),
            "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
            "flagged_cases": flagged, "nearest_by_case": best,
            "status": "review_required" if flagged else "no_lexical_flags",
            "limitation": "Triage only; misses semantic paraphrases and partial copies diluted by longer context. No semantic or pretraining contamination certification."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.train, args.cases), ensure_ascii=False, indent=2))
