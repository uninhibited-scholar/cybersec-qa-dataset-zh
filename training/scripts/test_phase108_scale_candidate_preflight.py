import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from phase108_scale_candidate_preflight import verify


class ScaleCandidatePreflightTest(unittest.TestCase):
    source_hash = "a" * 64

    def create_candidate(self, directory: Path, *, alpha=160.0, effective=20.0):
        (directory / "adapters.safetensors").write_bytes(b"adapter")
        (directory / "manifest.json").write_text(json.dumps({
            "kind": "phase108_cuda_recovery_candidate",
            "input_mlx_adapter_sha256": self.source_hash,
            "test_split_read": False,
            "lora": {"rank": 8, "mlx_scale": 20.0,
                     "peft_lora_alpha": alpha, "peft_effective_scale": effective},
        }))

    def test_valid_scale_provenance_passes_without_inference(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.create_candidate(directory)
            result = verify(directory, self.source_hash)
            self.assertEqual(result["status"], "scale_preflight_passed_no_inference")
            self.assertEqual(result["candidate_adapter_sha256"],
                             hashlib.sha256(b"adapter").hexdigest())

    def test_mismatched_effective_scale_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.create_candidate(directory, alpha=20.0, effective=2.5)
            with self.assertRaisesRegex(ValueError, "alpha/rank"):
                verify(directory, self.source_hash)


if __name__ == "__main__":
    unittest.main()
