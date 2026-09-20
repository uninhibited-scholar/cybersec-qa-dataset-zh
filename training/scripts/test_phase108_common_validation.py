import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from phase108_common_validation import validation_rows


class ValidationTests(unittest.TestCase):
    def test_validation_integrity_and_split_boundary(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "valid.jsonl"
            raw = json.dumps({"prompt": "question", "completion": "answer"}).encode()
            path.write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest()
            self.assertEqual(len(validation_rows(path, digest)), 1)
            with self.assertRaises(ValueError):
                validation_rows(path, "0" * 64)
            with self.assertRaises(ValueError):
                validation_rows(Path(root) / "test.jsonl", digest)

    def test_empty_target_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "valid.jsonl"
            raw = b'{"prompt":"question","completion":""}'
            path.write_bytes(raw)
            with self.assertRaises(ValueError):
                validation_rows(path, hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    unittest.main()
