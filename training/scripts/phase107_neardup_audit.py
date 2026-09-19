"""Targeted character n-gram near-duplicate scan for a private eval manifest.

The report contains IDs and similarities, never prompt text. This is a lexical
triage aid, not a semantic-equivalence proof; flagged pairs need human review.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path


def normalize(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE)


def features(text):
    text = normalize(text)
    grams = Counter()
    for size in (3, 4, 5):
        grams.update(text[i:i + size] for i in range(max(0, len(text) - size + 1)))
    return grams


def audit(path, threshold=0.52, top_n=100):
    raw = path.read_bytes()
    cases = json.loads(raw)
    if len({case["id"] for case in cases}) != len(cases):
        raise ValueError("manifest IDs must be unique")
    vectors = [features(case["prompt"]) for case in cases]
    df = Counter(feature for vector in vectors for feature in vector)
    n = len(cases)
    weights = []
    norms = []
    for vector in vectors:
        weighted = {feature: count * (math.log((n + 1) / (df[feature] + 1)) + 1)
                    for feature, count in vector.items()}
        weights.append(weighted)
        norms.append(math.sqrt(sum(value * value for value in weighted.values())))

    pairs = []
    category_max = defaultdict(lambda: {"similarity": 0.0, "pair": None})
    for left in range(n):
        for right in range(left + 1, n):
            small, large = (weights[left], weights[right]) if len(weights[left]) < len(weights[right]) else (weights[right], weights[left])
            dot = sum(value * large.get(feature, 0.0) for feature, value in small.items())
            similarity = dot / (norms[left] * norms[right]) if norms[left] and norms[right] else 0.0
            a, b = cases[left], cases[right]
            if a["category"] == b["category"]:
                summary = category_max[a["category"]]
                if similarity > summary["similarity"]:
                    summary.update(similarity=similarity, pair=[a["id"], b["id"]])
            if similarity >= threshold:
                pairs.append({"ids": [a["id"], b["id"]], "categories": [a["category"], b["category"]],
                              "similarity": round(similarity, 4)})
    pairs.sort(key=lambda row: row["similarity"], reverse=True)
    return {
        "status": "manual_review_required" if pairs else "no_pairs_above_lexical_threshold_not_semantic_certification",
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "cases": n,
        "method": "NFKC/casefold; TF-IDF weighted character 3/4/5-gram cosine",
        "threshold": threshold,
        "pairs_above_threshold": len(pairs),
        "pairs": pairs[:top_n],
        "omitted_flagged_pairs": max(0, len(pairs) - top_n),
        "max_within_category": {key: {"similarity": round(value["similarity"], 4), "pair": value["pair"]}
                                for key, value in sorted(category_max.items())},
        "limitation": "Lexical similarity finds templated wording but can miss semantic paraphrases and can flag distinct cases with shared instructions. Review flagged IDs in the local private manifest.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--threshold", type=float, default=0.10,
                        help="low lexical-triage threshold; review flags manually, not a semantic duplicate verdict")
    parser.add_argument("--top", type=int, default=100)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.manifest, threshold=args.threshold, top_n=args.top)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered)
