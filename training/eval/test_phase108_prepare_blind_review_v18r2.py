import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import phase108_prepare_blind_review_v18r2 as packer


def synthetic_inputs():
    categories = sorted(packer.EXPECTED_STRATA)
    cases, keys, responses = [], [], []
    for index in range(packer.EXPECTED_CASES):
        case_id = f"synthetic-{index:03d}"
        category = categories[index // 40]
        cases.append({
            "id": case_id,
            "category": category,
            "messages": [{"role": "user", "content": f"Synthetic prompt {index}"}],
        })
        keys.append({
            "id": case_id,
            "must_cover": ["synthetic criterion"],
            "must_not_claim": ["synthetic unsupported claim"],
            "evidence_boundary": "synthetic boundary",
            "format_contract": "synthetic format",
        })
        for alias in sorted(packer.ALIASES):
            content = f"synthetic response {alias} {index}"
            responses.append({
                "case_id": case_id,
                "alias": alias,
                "response": content,
                "response_sha256": hashlib.sha256(content.encode()).hexdigest(),
                "empty": False,
                "finish_reason": "stop",
                "generated_tokens": 7,
                "latency_seconds": 0.25,
                "tool_marker": False,
                "unclosed_thinking": False,
            })
    return cases, keys, responses


class BlindReviewBundleTests(unittest.TestCase):
    def test_reads_blind_alias_from_verified_filename(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            for alias in sorted(packer.ALIASES):
                (run_dir / f"responses-{alias}.jsonl").write_text(
                    json.dumps({"case_id": "synthetic", "response": "opaque"}) + "\n",
                    encoding="utf-8",
                )
            rows = packer.read_blinded_response_files(run_dir)
        self.assertEqual({row["alias"] for row in rows}, packer.ALIASES)
        self.assertTrue(all(row["response"] == "opaque" for row in rows))

    def test_rejects_row_alias_that_conflicts_with_verified_filename(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            alias = sorted(packer.ALIASES)[0]
            other_alias = sorted(packer.ALIASES - {alias})[0]
            (run_dir / f"responses-{alias}.jsonl").write_text(
                json.dumps({"case_id": "synthetic", "alias": other_alias,
                            "response": "opaque"}) + "\n",
                encoding="utf-8",
            )
            for remaining_alias in packer.ALIASES - {alias}:
                (run_dir / f"responses-{remaining_alias}.jsonl").write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "conflicts with its blinded filename"):
                packer.read_blinded_response_files(run_dir)

    def test_builds_complete_deterministic_blinded_matrix(self):
        cases, keys, responses = synthetic_inputs()
        first = packer.build_review_bundle(cases, keys, responses, seed=41)
        second = packer.build_review_bundle(cases, keys, responses, seed=41)
        self.assertEqual(first, second)
        self.assertEqual(len(first), packer.EXPECTED_CASES)
        for item in first:
            self.assertEqual({r["blind_alias"] for r in item["responses"]}, packer.ALIASES)
            self.assertIn(item["category"], packer.EXPECTED_STRATA)
            self.assertEqual(set(item["answer_key"]), set(packer.KEY_FIELDS))
            self.assertTrue(all("identity" not in key.lower() for key in item))

    def test_rejects_incomplete_response_matrix(self):
        cases, keys, responses = synthetic_inputs()
        with self.assertRaisesRegex(ValueError, "exactly 960"):
            packer.build_review_bundle(cases, keys, responses[:-1], seed=41)

    def test_rejects_response_digest_mismatch(self):
        cases, keys, responses = synthetic_inputs()
        responses[0]["response"] = "tampered"
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            packer.build_review_bundle(cases, keys, responses, seed=41)

    def test_rejects_missing_key_criterion(self):
        cases, keys, responses = synthetic_inputs()
        del keys[0]["format_contract"]
        with self.assertRaisesRegex(ValueError, "schema incomplete"):
            packer.build_review_bundle(cases, keys, responses, seed=41)

    def test_rejects_wrong_stratum_distribution(self):
        cases, keys, _ = synthetic_inputs()
        cases[0]["category"] = cases[40]["category"]
        with self.assertRaisesRegex(ValueError, "stratum counts"):
            packer.validate_case_and_key_rows(cases, keys)


if __name__ == "__main__":
    unittest.main()
