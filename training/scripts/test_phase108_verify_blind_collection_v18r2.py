from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import phase108_verify_blind_collection_v18r2 as verifier


def write_json(path: Path, value, mode: int = 0o600) -> bytes:
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path.write_bytes(raw)
    path.chmod(mode)
    return raw


class BlindCollectionVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.run_dir = self.root / "phase108-v18r2-blind-44803"
        self.run_dir.mkdir(mode=0o700)
        self.cases_path = self.root / "cases.json"
        self.freeze_path = self.root / "freeze.json"
        self.cases = [{"id": f"case-{i:03d}", "messages": [{"role": "user", "content": "x"}]}
                      for i in range(verifier.EXPECTED_ROWS)]
        cases_raw = write_json(self.cases_path, self.cases, mode=0o600)
        keys_sha = "a" * 64
        freeze = {
            "cases_sha256": hashlib.sha256(cases_raw).hexdigest(),
            "keys_sha256": keys_sha,
            "deployment_approval": False,
            "production_change": False,
        }
        freeze_raw = write_json(self.freeze_path, freeze, mode=0o600)
        self.pin_patches = patch.multiple(
            verifier,
            EXPECTED_CASES_SHA=hashlib.sha256(cases_raw).hexdigest(),
            EXPECTED_FREEZE_SHA=hashlib.sha256(freeze_raw).hexdigest(),
            EXPECTED_KEY_SHA=keys_sha,
        )
        self.pin_patches.start()

        pins = {
            "suite_freeze_sha256": verifier.EXPECTED_FREEZE_SHA,
            "cases_sha256": verifier.EXPECTED_CASES_SHA,
            "answer_keys_sha256": verifier.EXPECTED_KEY_SHA,
            "candidate_sha256": verifier.EXPECTED_CANDIDATE_SHA,
            "parent_sha256": verifier.EXPECTED_PARENT_SHA,
            "base_config_sha256": verifier.EXPECTED_BASE_CONFIG_SHA,
            "base_index_sha256": verifier.EXPECTED_BASE_INDEX_SHA,
            "chat_template_sha256": verifier.EXPECTED_TEMPLATE_SHA,
            "system_prompt_sha256": verifier.EXPECTED_SYSTEM_PROMPT_SHA,
            "collector_sha256": verifier.EXPECTED_COLLECTOR_SHA,
            "job_script_sha256": verifier.EXPECTED_JOB_SCRIPT_SHA,
            "adapter_loader_sha256": verifier.EXPECTED_ADAPTER_LOADER_SHA,
        }
        common = {
            **pins,
            "evaluation": "phase108_v1.8-rev2_blind_raw_weight_collection",
            "blind": True,
            "scores": False,
            "promotion_eligible": False,
            "production_changed": False,
            "keys_opened": False,
            "inference": verifier.EXPECTED_INFERENCE,
        }
        write_json(self.run_dir / "run-manifest.json", {
            **common, "base_weight_shards": verifier.EXPECTED_BASE_SHARDS,
        })
        summaries = {}
        for alias in sorted(verifier.ALIASES):
            path = self.run_dir / f"responses-{alias}.jsonl"
            rows = []
            for case in self.cases:
                answer = "synthetic answer"
                rows.append({
                    "case_id": case["id"],
                    "response": answer,
                    "response_sha256": hashlib.sha256(answer.encode()).hexdigest(),
                    "response_chars": len(answer),
                    "empty": False,
                    "generated_tokens": 2,
                    "finish_reason": "stop",
                    "tool_marker": False,
                    "unclosed_thinking": False,
                    "latency_seconds": 0.1,
                    "blind": True,
                    "scored": False,
                })
            raw = b"".join((json.dumps(row, sort_keys=True) + "\n").encode() for row in rows)
            path.write_bytes(raw)
            path.chmod(0o600)
            summaries[alias] = {
                "responses_sha256": hashlib.sha256(raw).hexdigest(),
                "cases": verifier.EXPECTED_ROWS,
                "empty_count": 0,
                "tool_marker_count": 0,
                "unclosed_thinking_count": 0,
                "finish_reasons": {"stop": verifier.EXPECTED_ROWS},
            }
        aggregate = {
            **common,
            "inference": {k: v for k, v in verifier.EXPECTED_INFERENCE.items() if k != "case_count"},
            "summaries_by_blind_alias": summaries,
        }
        write_json(self.run_dir / "aggregate.json", aggregate)
        write_json(self.run_dir / "identity-map.json", {"base": "A", "parent": "B", "candidate": "C"})
        self.sacct_runner = lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args="sacct", returncode=0,
            stdout="44803|COMPLETED|0:0\n44803.batch|COMPLETED|0:0\n",
            stderr="",
        )

    def tearDown(self):
        self.pin_patches.stop()
        self.temp.cleanup()

    def test_verifies_all_arms_without_revealing_identity(self):
        report = verifier.verify_collection(
            self.run_dir, self.cases_path, self.freeze_path, "44803", self.sacct_runner
        )
        self.assertEqual(report["status"], "verified_blind_collection_integrity")
        self.assertEqual(set(report["summaries_by_blind_alias"]), verifier.ALIASES)
        self.assertTrue(all(arm["rows"] == verifier.EXPECTED_ROWS
                            for arm in report["summaries_by_blind_alias"].values()))
        self.assertFalse(report["identity_map_read"])
        self.assertFalse(report["labels_revealed"])
        self.assertNotIn("identity_map_sha256", report)
        self.assertFalse(report["capability_score"])
        self.assertFalse(report["deployment_approval"])

    def test_does_not_parse_identity_map_before_blind_scoring(self):
        (self.run_dir / "identity-map.json").write_text("not-json-and-still-sealed")
        (self.run_dir / "identity-map.json").chmod(0o600)
        report = verifier.verify_collection(
            self.run_dir, self.cases_path, self.freeze_path, "44803", self.sacct_runner
        )
        self.assertFalse(report["identity_map_read"])

    def test_rejects_nonterminal_job_before_reading_run_files(self):
        self.sacct_runner = lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args="sacct", returncode=0, stdout="44803|RUNNING|0:0\n", stderr=""
        )
        missing_dir = self.root / "not-created"
        with self.assertRaisesRegex(ValueError, "not COMPLETED"):
            verifier.verify_collection(
                missing_dir, self.cases_path, self.freeze_path, "44803", self.sacct_runner
            )

    def test_rejects_response_hash_mismatch_without_opening_identity_map(self):
        (self.run_dir / "identity-map.json").unlink()
        path = self.run_dir / "responses-A.jsonl"
        path.write_text(path.read_text().replace("synthetic answer", "changed answer", 1))
        path.chmod(0o600)
        with self.assertRaisesRegex(ValueError, "response file hash mismatch"):
            verifier.verify_collection(
                self.run_dir, self.cases_path, self.freeze_path, "44803", self.sacct_runner
            )


if __name__ == "__main__":
    unittest.main()
