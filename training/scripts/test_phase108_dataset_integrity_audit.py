import json
from pathlib import Path
import tempfile
import unittest

from phase108_dataset_integrity_audit import audit, input_texts


class DatasetIntegrityAuditTests(unittest.TestCase):
    def test_extracts_user_text_but_not_assistant_targets(self):
        row = {"messages": [
            {"role": "user", "content": "check this code"},
            {"role": "assistant", "content": "target answer"},
        ]}
        self.assertEqual(input_texts(row), {"check this code"})

    def test_finds_exact_cross_split_user_prompt_and_suite_overlap(self):
        key = b"k" * 32
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "train.jsonl").write_text(json.dumps({"prompt": "Same  prompt"}) + "\n")
            (root / "valid.jsonl").write_text(json.dumps({"messages": [{"role": "user", "content": "same prompt"}]}) + "\n")
            (root / "test.jsonl").write_text(json.dumps({"question": "different"}) + "\n")
            report = audit([root], key, {"dummy"})["dataset_dirs"][0]
        self.assertEqual(report["cross_split_exact_overlap_strings"]["train:valid"], 1)
        self.assertEqual(report["unique_user_strings"]["test"], 1)
        self.assertNotIn("Same  prompt", json.dumps(report))

    def test_counts_malformed_jsonl_lines_without_aborting(self):
        key = b"k" * 32
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "train.jsonl").write_text("not json\n" + json.dumps({"prompt": "ok"}) + "\n")
            report = audit([root], key, None)["dataset_dirs"][0]
        self.assertEqual(report["split_rows"]["train"], 1)
        self.assertEqual(report["split_parse_errors"]["train"], 1)

    def test_reports_cross_dataset_train_overlap_without_text(self):
        key = b"k" * 32
        with tempfile.TemporaryDirectory() as temp:
            left = Path(temp) / "left"
            right = Path(temp) / "right"
            left.mkdir()
            right.mkdir()
            (left / "train.jsonl").write_text(json.dumps({"prompt": "shared"}) + "\n")
            (right / "train.jsonl").write_text(json.dumps({"question": "SHARED"}) + "\n")
            report = audit([left, right], key, None)
        counts = list(report["cross_dataset_exact_user_string_overlap"].values())
        self.assertEqual(counts[0]["train"], 1)
        self.assertNotIn("shared", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
