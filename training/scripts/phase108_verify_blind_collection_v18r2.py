#!/usr/bin/env python3
"""Verify a completed Phase108 blind collection before revealing arm labels.

This verifier reads private response files only to check schema, row coverage,
and hashes. It never prints or exports prompts or response text. Run on the
cluster after ``sacct`` reports the collection job completed successfully.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys


EXPECTED_CASES_SHA = "c028b564d2273fc6779f248918511fa2bff0fe73abc4c7bb4ab6051ecc3b91c9"
EXPECTED_PARENT_SHA = "3ed1a85e7b021e14198332a525bfa4bb75b336a03579d526f8210f1576317036"
EXPECTED_CANDIDATE_SHA = "4e9177c3956aaa0c176929e7d8225b9882a2587b4dadad9cb51c04d905453772"
EXPECTED_FREEZE_SHA = "1dd603084fe3f026954ead8cb55004514b1c5b43a3b3219b0b10b0489ac0d5bf"
EXPECTED_KEY_SHA = "f79828a550fb80cd84aba7faa593cd84a4f47e08ee8afc358957726de17a4015"
EXPECTED_BASE_CONFIG_SHA = "260a51b7a10e45b682d6f4b3535b6fca3a7e42e1e55361c177e2c9f3ade27650"
EXPECTED_BASE_INDEX_SHA = "5e699a61da09415f33a625885364d3889a80acb6ab88aedaf6e195b2612addf4"
EXPECTED_TEMPLATE_SHA = "9287fdda1d9257e0bdebaa2eac2db569a6cfc64d3b3ac1b812edd29f583bbc86"
EXPECTED_SYSTEM_PROMPT_SHA = "8ece8f47d1fcdca21bdcc8174539ad29182bbaaaf3eb7b303d5536aaaf53ade5"
EXPECTED_COLLECTOR_SHA = "9a1efefb3f02080e459ffbf6ec8f9052129b4595f0061e104ea6cc007f9d2a64"
EXPECTED_JOB_SCRIPT_SHA = "9599873ebaaf53b44d2d850ff49170f2de3950c574f6d38a4864d966ddc4fe30"
EXPECTED_ADAPTER_LOADER_SHA = "00ef5d3b1aaada8285b711a68f47c9e00a4fb9dbbd993e8eaf8eefd7426fa371"
EXPECTED_BASE_SHARDS = {
    "model-00001-of-00002.safetensors": "25094f7fbaef4769da447cb6ebf4a39d99ccc5043856cce1b4f8fc2f91ed9115",
    "model-00002-of-00002.safetensors": "a2fd70328fc4fb518bb40ac806e8c05f21ad12e228648684775f67c28104815d",
}
EXPECTED_INFERENCE = {
    "case_count": 320,
    "max_new_tokens": 700,
    "temperature": 0.12,
    "top_p": 0.9,
    "top_k": 0,
    "repetition_penalty": 1.12,
    "repetition_window": 128,
    "adapter_scale": 20.0,
    "tools": [],
    "seed": "sha256(case_id) shared across arms",
}
EXPECTED_ROWS = 320
ALIASES = {"A", "B", "C"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid or unreadable JSON artifact: {path.name}") from exc


def require_private(path: Path, directory: bool = False) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise ValueError(f"artifact is not private: {path.name}")
    if directory and mode != 0o700:
        raise ValueError("output directory mode must be 0700")


def verify_slurm(job_id: str, runner=subprocess.run) -> dict:
    result = runner(
        ["sacct", "-n", "-P", "-j", job_id, "--format=JobIDRaw,State,ExitCode"],
        check=True, capture_output=True, text=True, timeout=15,
    )
    records = []
    for line in result.stdout.splitlines():
        fields = line.strip().split("|")
        if len(fields) == 3 and fields[0] == job_id:
            records.append(fields)
    if len(records) != 1:
        raise ValueError("could not verify one authoritative Slurm job record")
    _, state, exit_code = records[0]
    if state.split()[0] != "COMPLETED" or exit_code != "0:0":
        raise ValueError("collection Slurm job is not COMPLETED with exit code 0")
    return {"job_id": job_id, "state": state, "exit_code": exit_code}


def verify_collection(run_dir: Path, cases_path: Path, freeze_path: Path,
                      job_id: str, slurm_runner=subprocess.run) -> dict:
    slurm = verify_slurm(job_id, slurm_runner)
    require_private(run_dir, directory=True)

    manifest_path = run_dir / "run-manifest.json"
    aggregate_path = run_dir / "aggregate.json"
    require_private(manifest_path)
    require_private(aggregate_path)
    cases_path = Path(cases_path)
    freeze_path = Path(freeze_path)
    manifest = read_json(manifest_path)
    aggregate = read_json(aggregate_path)
    cases_raw = cases_path.read_bytes()
    freeze_raw = freeze_path.read_bytes()
    cases_sha = hashlib.sha256(cases_raw).hexdigest()
    freeze_sha = hashlib.sha256(freeze_raw).hexdigest()
    if cases_sha != EXPECTED_CASES_SHA or freeze_sha != EXPECTED_FREEZE_SHA:
        raise ValueError("frozen suite hash mismatch")
    freeze = json.loads(freeze_raw)
    if (freeze.get("cases_sha256") != EXPECTED_CASES_SHA or
            freeze.get("keys_sha256") != EXPECTED_KEY_SHA or
            freeze.get("deployment_approval") is not False or
            freeze.get("production_change") is not False):
        raise ValueError("frozen suite manifest mismatch")
    rows = json.loads(cases_raw)
    if not isinstance(rows, list) or len(rows) != EXPECTED_ROWS:
        raise ValueError("frozen case count mismatch")
    expected_ids = {row.get("id") for row in rows}
    if None in expected_ids or len(expected_ids) != EXPECTED_ROWS:
        raise ValueError("frozen case IDs are invalid")

    pinned = {
        "suite_freeze_sha256": EXPECTED_FREEZE_SHA,
        "cases_sha256": EXPECTED_CASES_SHA,
        "answer_keys_sha256": EXPECTED_KEY_SHA,
        "candidate_sha256": EXPECTED_CANDIDATE_SHA,
        "parent_sha256": EXPECTED_PARENT_SHA,
        "base_config_sha256": EXPECTED_BASE_CONFIG_SHA,
        "base_index_sha256": EXPECTED_BASE_INDEX_SHA,
        "chat_template_sha256": EXPECTED_TEMPLATE_SHA,
        "system_prompt_sha256": EXPECTED_SYSTEM_PROMPT_SHA,
        "collector_sha256": EXPECTED_COLLECTOR_SHA,
        "job_script_sha256": EXPECTED_JOB_SCRIPT_SHA,
        "adapter_loader_sha256": EXPECTED_ADAPTER_LOADER_SHA,
    }
    for artifact_name, artifact in (("run manifest", manifest), ("aggregate", aggregate)):
        for field, expected in pinned.items():
            if artifact.get(field) != expected:
                raise ValueError(f"{artifact_name} pin mismatch: {field}")
    for artifact_name, artifact in (("run manifest", manifest), ("aggregate", aggregate)):
        if (artifact.get("blind") is not True or artifact.get("scores") is not False or
                artifact.get("promotion_eligible") is not False or
                artifact.get("production_changed") is not False or
                artifact.get("keys_opened") is not False):
            raise ValueError(f"{artifact_name} guardrail flag mismatch")
    if manifest.get("evaluation") != "phase108_v1.8-rev2_blind_raw_weight_collection":
        raise ValueError("run manifest evaluation identifier mismatch")
    if aggregate.get("evaluation") != manifest.get("evaluation"):
        raise ValueError("aggregate evaluation identifier mismatch")
    if manifest.get("base_weight_shards") != EXPECTED_BASE_SHARDS:
        raise ValueError("base model shard inventory mismatch")
    expected_aggregate_inference = {k: v for k, v in EXPECTED_INFERENCE.items() if k != "case_count"}
    if manifest.get("inference") != EXPECTED_INFERENCE:
        raise ValueError("run manifest inference protocol mismatch")
    if aggregate.get("inference") != expected_aggregate_inference:
        raise ValueError("aggregate inference protocol mismatch")

    alias_summaries = aggregate.get("summaries_by_blind_alias")
    if not isinstance(alias_summaries, dict) or set(alias_summaries) != ALIASES:
        raise ValueError("aggregate must contain exactly the three blinded arms")
    verified_alias_stats = {}
    for alias in sorted(ALIASES):
        response_path = run_dir / f"responses-{alias}.jsonl"
        require_private(response_path)
        response_sha = sha256_file(response_path)
        summary = alias_summaries[alias]
        if summary.get("responses_sha256") != response_sha:
            raise ValueError(f"response file hash mismatch for alias {alias}")
        seen_ids = set()
        counters = {"empty": 0, "tool_marker": 0, "unclosed_thinking": 0}
        finish_reasons: dict[str, int] = {}
        count = 0
        with response_path.open(encoding="utf-8") as stream:
            for line in stream:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"malformed response JSONL for alias {alias}") from exc
                case_id = record.get("case_id")
                if case_id not in expected_ids or case_id in seen_ids:
                    raise ValueError(f"missing, unknown, or duplicate case id for alias {alias}")
                seen_ids.add(case_id)
                answer = record.get("response")
                if not isinstance(answer, str):
                    raise ValueError(f"response schema mismatch for alias {alias}")
                if record.get("response_sha256") != hashlib.sha256(answer.encode()).hexdigest():
                    raise ValueError(f"per-response hash mismatch for alias {alias}")
                if record.get("response_chars") != len(answer) or record.get("empty") is not (not answer.strip()):
                    raise ValueError(f"response metadata mismatch for alias {alias}")
                if record.get("blind") is not True or record.get("scored") is not False:
                    raise ValueError(f"response guardrail mismatch for alias {alias}")
                if not isinstance(record.get("tool_marker"), bool) or not isinstance(record.get("unclosed_thinking"), bool):
                    raise ValueError(f"response flag schema mismatch for alias {alias}")
                finish = record.get("finish_reason")
                if finish not in {"length", "stop", "other_stop"}:
                    raise ValueError(f"finish reason mismatch for alias {alias}")
                counters["empty"] += int(record["empty"])
                counters["tool_marker"] += int(record["tool_marker"])
                counters["unclosed_thinking"] += int(record["unclosed_thinking"])
                finish_reasons[finish] = finish_reasons.get(finish, 0) + 1
                count += 1
        if count != EXPECTED_ROWS or seen_ids != expected_ids or summary.get("cases") != EXPECTED_ROWS:
            raise ValueError(f"case coverage mismatch for alias {alias}")
        if any(summary.get(f"{field}_count") != value for field, value in counters.items()):
            raise ValueError(f"aggregate counter mismatch for alias {alias}")
        if summary.get("finish_reasons") != finish_reasons:
            raise ValueError(f"aggregate finish-reason mismatch for alias {alias}")
        verified_alias_stats[alias] = {
            "rows": count,
            "empty": counters["empty"],
            "tool_markers": counters["tool_marker"],
            "unclosed_thinking": counters["unclosed_thinking"],
            "finish_reasons": finish_reasons,
            "responses_sha256": response_sha,
        }

    # Preserve blinding for the independent scorer. Check that the sealed map
    # exists and is private, but do not read, hash, or emit its contents here.
    identity_path = run_dir / "identity-map.json"
    require_private(identity_path)
    return {
        "status": "verified_blind_collection_integrity",
        "slurm": slurm,
        "rows_per_arm": EXPECTED_ROWS,
        "identity_map_read": False,
        "labels_revealed": False,
        "candidate_sha256": EXPECTED_CANDIDATE_SHA,
        "parent_sha256": EXPECTED_PARENT_SHA,
        "freeze_sha256": freeze_sha,
        "cases_sha256": cases_sha,
        "summaries_by_blind_alias": verified_alias_stats,
        "capability_score": False,
        "deployment_approval": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    try:
        report = verify_collection(args.run_dir, args.cases, args.freeze, args.job_id)
    except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "rejected", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
