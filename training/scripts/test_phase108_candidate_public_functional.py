import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from phase108_candidate_public_functional import run


class CandidatePublicFunctionalTests(unittest.TestCase):
    def test_only_aggregate_metadata_is_saved(self):
        private = "must not persist this generated text"

        def fake_request(url, payload=None, timeout=300):
            if url.endswith("/health"):
                return 200, {"status": "ok"}
            if url.endswith("/v1/models"):
                return 200, {"data": []}
            if payload and payload.get("tools"):
                return 400, {"error": {"message": private}}
            return 200, {"choices": [{"message": {"content": private}, "finish_reason": "stop"}]}

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "summary.json"
            with patch("phase108_candidate_public_functional.request_json", side_effect=fake_request):
                result = run("http://127.0.0.1:21808", output, 20.0, "a" * 64)
            saved = output.read_text()
        self.assertEqual(result["nonempty_count"], 4)
        self.assertEqual(result["empty_count"], 0)
        self.assertTrue(result["tool_request_rejected"])
        self.assertNotIn(private, saved)
        self.assertNotIn(private, json.dumps(result))


if __name__ == "__main__":
    unittest.main()
