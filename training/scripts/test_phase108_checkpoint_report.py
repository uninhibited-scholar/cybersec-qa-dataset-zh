import tempfile
from pathlib import Path
import unittest

from phase108_checkpoint_report import report


class CheckpointReportTests(unittest.TestCase):
    def check_report(self, log, files):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            source = root / "run.log"
            source.write_text(log)
            for name in files:
                (root / name).write_bytes(b"fixture")
            return report(source, root)

    def test_no_checkpoint_is_not_ready(self):
        result = self.check_report("Iter 1: Val loss 1.2", ["adapters.safetensors"])
        self.assertEqual(result["status"], "waiting_for_validated_checkpoint")

    def test_test_loss_does_not_drive_selection(self):
        result = self.check_report("Iter 1000: Val loss 2.0\nIter 2000: Val loss 2.1\nTest loss 0.1",
                                   ["0001000_adapters.safetensors", "0002000_adapters.safetensors"])
        self.assertIsNone(result["suggested_for_behavior_evaluation"])
        self.assertEqual(result["status"], "requires_common_validation")
        self.assertEqual([item["step"] for item in result["validated_checkpoints"]], [1000, 2000])
        self.assertFalse(result["production_approval"])

    def test_conflicting_or_nonfinite_loss_blocks_selection(self):
        for log in ("Iter 1000: Val loss nan", "Iter 1000: Val loss 1\nIter 1000: Val loss 2"):
            result = self.check_report(log, ["0001000_adapters.safetensors"])
            self.assertEqual(result["status"], "invalid")
            self.assertIsNone(result["suggested_for_behavior_evaluation"])

    def test_missing_validation_is_excluded(self):
        result = self.check_report("Iter 1: Val loss 1", ["0001000_adapters.safetensors"])
        self.assertEqual(result["checkpoint_steps_without_validation"], [1000])
        self.assertIsNone(result["suggested_for_behavior_evaluation"])


if __name__ == "__main__":
    unittest.main()
