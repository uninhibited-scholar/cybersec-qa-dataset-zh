from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from phase107_prepare_critical_adjudication import (
    expected_rows,
    ledger_rows,
    secure_write,
    validate_ledger,
)


class AdjudicationPacketTests(unittest.TestCase):
    def test_expected_bundle_requires_320_three_arm_responses(self) -> None:
        bundle = [
            {
                "case_id": f"case-{i}",
                "responses": [
                    {"blind_alias": alias, "classification": "ok"}
                    for alias in ("A", "B", "C")
                ],
            }
            for i in range(320)
        ]
        self.assertEqual(len(expected_rows(bundle)), 960)
        with self.assertRaises(ValueError):
            expected_rows(bundle[:-1])

    def test_rejects_duplicate_ledger_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reviewer-a-test.jsonl"
            record = {
                "row": 1,
                "case_id": "case-0",
                "alias": "A",
                "critical": False,
                "scores": [2, 2, 2, 2],
            }
            path.write_text(json.dumps(record) + "\n" + json.dumps(record) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                ledger_rows([path], "A")

    def test_validator_accepts_only_complete_matching_keys(self) -> None:
        expected = {
            (1, "case-0", alias): {
                "case": {},
                "response": {"classification": "ok"},
            }
            for alias in ("A", "B", "C")
        }
        rows = {
            key: {
                "row": key[0],
                "case_id": key[1],
                "alias": key[2],
                "response_state": "ok",
                "critical": False,
                "scores": [1, 1, 1, 1],
            }
            for key in expected
        }
        self.assertEqual(validate_ledger("A", rows, expected), 0)
        del rows[(1, "case-0", "C")]
        with self.assertRaisesRegex(ValueError, "missing=1"):
            validate_ledger("A", rows, expected)

    def test_secure_write_sets_private_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "private" / "out.jsonl"
            secure_write(path, "{}\n")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)


if __name__ == "__main__":
    unittest.main()
