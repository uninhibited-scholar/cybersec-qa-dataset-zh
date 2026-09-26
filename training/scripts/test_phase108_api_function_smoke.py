import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from phase108_api_function_smoke import run


class ApiFunctionSmokeTests(unittest.TestCase):
    def test_writes_only_response_metadata_and_checks_tool_rejection(self):
        calls = 0

        def fake_request(url, payload=None, timeout=300):
            nonlocal calls
            calls += 1
            if url.endswith("/health"):
                return 200, {"status": "ok", "sandbox": True}
            if url.endswith("/v1/models"):
                return 200, {"data": [{"id": "phase108-candidate", "object": "model"}]}
            if payload and payload.get("tools"):
                return 400, {"error": {"message": "sandbox evaluator has no tools"}}
            return 200, {"choices": [{"message": {"content": "private response text"}, "finish_reason": "stop"}]}

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "summary.json"
            with patch("phase108_api_function_smoke.request_json", side_effect=fake_request):
                result = run("http://127.0.0.1:21808", output, 5.0)
            saved = output.read_text()
        self.assertEqual(calls, 4)
        self.assertTrue(result["chat_nonempty"])
        self.assertTrue(result["tool_request_rejected"])
        self.assertNotIn("private response text", saved)
        self.assertNotIn("private response text", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
