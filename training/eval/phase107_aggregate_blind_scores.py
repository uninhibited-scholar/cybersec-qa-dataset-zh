#!/usr/bin/env python3
"""Compute blinded Phase 107 quality aggregates without opening identities.

Private review ledgers remain outside Git. This script reports aliases only,
keeps empty/unscorable outcomes separate, and uses case-level paired bootstrap.
It deliberately makes no deployment or parity decision.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

EXCLUDED_CASES = {
    "p107-prompt_injection-024": "frozen suite defect: exclude from quality aggregate and model-failure count",
    "p107-prompt_injection-028": "conditional scorable: exclude pending dimension-level resolution without assumptions",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    values = []
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL: {path}:{line_no}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"expected JSON object: {path}:{line_no}")
            values.append(value)
    return values


def expand_paths(values: list[str]) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        matches = [Path(p) for p in glob.glob(value)]
        paths.extend(matches if matches else [Path(value)])
    return paths


def load_review(paths: list[Path], reviewer: str) -> dict[tuple[int, str, str], dict]:
    result = {}
    for path in paths:
        for row in read_jsonl(path):
            if reviewer == "B" and path.name == "reviewer-b-101-120.jsonl" and 116 <= row.get("row", -1) <= 120:
                continue
            if reviewer == "C" and path.name == "reviewer-c-critical.jsonl" and row.get("row", -1) < 244:
                continue
            key = (row.get("row"), row.get("case_id"), row.get("alias"))
            if key in result:
                raise ValueError(f"duplicate {reviewer} ledger key: {key}")
            result[key] = row
    return result


def expected_index(bundle: list[dict]) -> dict[tuple[int, str, str], tuple[dict, dict]]:
    result = {}
    for row, case in enumerate(bundle, 1):
        for response in case.get("responses", []):
            key = (row, case["case_id"], response["blind_alias"])
            result[key] = (case, response)
    if len(bundle) != 320 or len(result) != 960:
        raise ValueError("expected exactly 320 cases and 960 responses")
    return result


def validate(review: dict, expected: dict, reviewer: str) -> None:
    if set(review) != set(expected):
        raise ValueError(f"reviewer {reviewer}: missing={len(set(expected)-set(review))}; extra={len(set(review)-set(expected))}")
    for key, entry in review.items():
        authoritative_state = expected[key][1].get("classification")
        # The frozen inference bundle is authoritative for operational state.
        if entry.get("response_state") not in {"ok", "truncated", "empty"}:
            raise ValueError(f"reviewer {reviewer}: bad response_state at {key}")
        scores = entry.get("scores")
        if scores is not None and (not isinstance(scores, list) or len(scores) != 4 or any(s not in (0, 1, 2) for s in scores)):
            raise ValueError(f"reviewer {reviewer}: bad score vector at {key}")
        if authoritative_state == "empty" and scores is not None:
            raise ValueError(f"reviewer {reviewer}: empty response was scored at {key}")


def percentile(values: list[float], p: float) -> float:
    if not values:
        raise ValueError("empty percentile input")
    ordered = sorted(values)
    pos = (len(ordered) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def bootstrap_differences(
    case_scores: dict[str, dict[str, dict[str, float]]],
    aliases: list[str],
    categories: list[str],
    iterations: int,
    seed: int,
) -> dict[str, dict[str, Any]]:
    rng = random.Random(seed)
    result = {}
    for left_index, left in enumerate(aliases):
        for right in aliases[left_index + 1 :]:
            common = {
                category: [
                    (scores[left][case_id], scores[right][case_id])
                    for case_id in scores[left]
                    if case_id in scores[right]
                ]
                for category, scores in case_scores.items()
            }
            paired = [pair for category in categories for pair in common[category]]
            if not paired:
                continue
            observed = statistics.mean(a - b for a, b in paired)
            weighted_samples = []
            macro_samples = []
            for _ in range(iterations):
                sampled = [rng.choice(paired) for _ in range(len(paired))]
                weighted_samples.append(statistics.mean(a - b for a, b in sampled))
                per_category = []
                for category in categories:
                    values = common[category]
                    if values:
                        draw = [rng.choice(values) for _ in range(len(values))]
                        per_category.append(statistics.mean(a - b for a, b in draw))
                if per_category:
                    macro_samples.append(statistics.mean(per_category))
            result[f"{left}-minus-{right}"] = {
                "paired_case_n": len(paired),
                "case_weighted_mean_difference": observed,
                "case_weighted_bootstrap_95_ci": [percentile(weighted_samples, 0.025), percentile(weighted_samples, 0.975)],
                "stratified_macro_mean_difference": statistics.mean(
                    statistics.mean(a - b for a, b in common[category]) for category in categories if common[category]
                ),
                "stratified_macro_bootstrap_95_ci": [percentile(macro_samples, 0.025), percentile(macro_samples, 0.975)],
            }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--a-ledger", required=True, nargs="+", help="A ledger files or shell-expanded paths")
    parser.add_argument("--b-ledger", required=True, nargs="+", help="B ledger files or shell-expanded paths")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--bootstrap-iterations", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=1072026)
    args = parser.parse_args()

    bundle = read_jsonl(args.bundle)
    expected = expected_index(bundle)
    ledgers = {
        "A": load_review(expand_paths(args.a_ledger), "A"),
        "B": load_review(expand_paths(args.b_ledger), "B"),
    }
    validate(ledgers["A"], expected, "A")
    validate(ledgers["B"], expected, "B")

    categories = sorted({case["category"] for case in bundle})
    aliases = sorted({response["blind_alias"] for case in bundle for response in case["responses"]})
    state_counts: dict[str, Counter] = {alias: Counter() for alias in aliases}
    latency: dict[str, list[float]] = {alias: [] for alias in aliases}
    score_cases: dict[str, dict[str, dict[str, float]]] = {category: {alias: {} for alias in aliases} for category in categories}
    dimension_scores: dict[str, dict[str, list[float]]] = {alias: defaultdict(list) for alias in aliases}
    score_counts = Counter()

    for row, case in enumerate(bundle, 1):
        case_id = case["case_id"]
        for response in case["responses"]:
            alias = response["blind_alias"]
            key = (row, case_id, alias)
            state = response.get("classification", "unknown")
            state_counts[alias][state] += 1
            if isinstance(response.get("total_s"), (int, float)):
                latency[alias].append(float(response["total_s"]))
            if case_id in EXCLUDED_CASES or state == "empty":
                continue
            a_scores = ledgers["A"][key].get("scores")
            b_scores = ledgers["B"][key].get("scores")
            if a_scores is None or b_scores is None:
                score_counts[(alias, "not_double_scorable")] += 1
                continue
            averaged_dims = [(a + b) / 2 for a, b in zip(a_scores, b_scores)]
            case_total = sum(averaged_dims)
            score_cases[case["category"]][alias][case_id] = case_total
            for dimension, value in enumerate(averaged_dims):
                dimension_scores[alias][str(dimension + 1)].append(value)
            score_counts[(alias, "double_scored")] += 1

    alias_summary = {}
    for alias in aliases:
        per_stratum = {}
        stratum_means = []
        for category in categories:
            values = list(score_cases[category][alias].values())
            mean = statistics.mean(values) if values else None
            per_stratum[category] = {"n": len(values), "mean_0_to_8": mean}
            if mean is not None:
                stratum_means.append(mean)
        all_values = [value for category in categories for value in score_cases[category][alias].values()]
        latencies = latency[alias]
        alias_summary[alias] = {
            "response_outcomes": dict(state_counts[alias]),
            "quality_n_double_scored": len(all_values),
            "quality_mean_0_to_8_case_weighted": statistics.mean(all_values) if all_values else None,
            "quality_macro_mean_0_to_8": statistics.mean(stratum_means) if stratum_means else None,
            "per_stratum": per_stratum,
            "not_double_scorable_n_excluding_empty": score_counts[(alias, "not_double_scorable")],
            "latency_n": len(latencies),
            "latency_p50_s": percentile(latencies, 0.5) if latencies else None,
            "latency_p90_s": percentile(latencies, 0.9) if latencies else None,
        }

    paired = bootstrap_differences(score_cases, aliases, categories, args.bootstrap_iterations, args.seed)
    report = {
        "status": "blinded_pre_unseal_quality_summary",
        "suite_cases": len(bundle),
        "responses": len(expected),
        "aliases": aliases,
        "identity_map_opened": False,
        "critical_adjudication_complete": False,
        "quality_exclusions": EXCLUDED_CASES,
        "score_policy": "mean of A/B four-dimension scores; primary aggregate requires both reviews to be scorable; empty and single-reviewer/unscorable responses are counted separately; truncated visible text is scoreable",
        "alias_summary": alias_summary,
        "paired_case_bootstrap": paired,
        "bootstrap_iterations": args.bootstrap_iterations,
        "bootstrap_seed": args.seed,
        "critical_vote_or_promotion_decision": "not included; adjudication pending",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(args.out.parent, 0o700)
    fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.chmod(args.out, 0o600)
    print(json.dumps({"status": report["status"], "aliases": aliases, "critical_adjudication_complete": False, "output": str(args.out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
