import json
import random
import tempfile
import unittest
from pathlib import Path

from training.scripts.phase108_greedy_exposed_replay import (
    EXPECTED_CASE_IDS,
    select_cases,
    summarize,
)


class GreedyExposedReplayTest(unittest.TestCase):
    def test_select_cases_pins_the_exposed_sample_and_hash(self):
        # Construct a deterministic fixture whose seeded sample matches the
        # already exposed IDs, without importing or printing private prompts.
        positions = random.Random(20260925).sample(range(16), 16)
        rows = [{"id": "unused-%02d" % index, "messages": []} for index in range(16)]
        for position, case_id in zip(positions, EXPECTED_CASE_IDS):
            rows[position]["id"] = case_id
        encoded = json.dumps(rows).encode()
        import hashlib
        digest = hashlib.sha256(encoded).hexdigest()
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "cases.json"
            source.write_bytes(encoded)
            observed, selected = select_cases(source, digest)
        self.assertEqual(observed, digest)
        self.assertEqual([row["id"] for row in selected], EXPECTED_CASE_IDS)

    def test_select_cases_refuses_modified_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "cases.json"
            source.write_text("[]\n")
            with self.assertRaisesRegex(ValueError, "case source hash mismatch"):
                select_cases(source, "0" * 64)

    def test_summary_contains_only_aggregate_metadata(self):
        rows = [
            {"empty": True, "finish_reason": "stop", "chars": 0},
            {"empty": False, "finish_reason": "length", "chars": 40},
        ]
        result = summarize(rows)
        self.assertEqual(result["empty"], 1)
        self.assertEqual(result["nonempty"], 1)
        self.assertEqual(result["finish_reasons"], {"stop": 1, "length": 1})
        self.assertNotIn("prompt", result)
        self.assertNotIn("response", result)


if __name__ == "__main__":
    unittest.main()
