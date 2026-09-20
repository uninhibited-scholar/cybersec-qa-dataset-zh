import sys
import unittest
from pathlib import PurePosixPath
from unittest.mock import patch

sys.path.insert(0, str(__file__.replace("test_phase108_checkpoint_backup.py", "")))
import phase108_checkpoint_backup as backup


class CheckpointBackupTests(unittest.TestCase):
    def test_plan_reports_hash_without_copying(self):
        digest = b"a" * 64 + b"  checkpoint\n"
        with patch.object(backup, "_remote", side_effect=[digest, b"clear\n"]) as remote:
            result = backup.plan("mini", "cluster", PurePosixPath("/a.ckpt"), PurePosixPath("/b.ckpt"))
        self.assertEqual(result["status"], "ready_to_copy")
        self.assertEqual(result["source_sha256"], "a" * 64)
        self.assertEqual(remote.call_count, 2)

    def test_plan_refuses_existing_destination(self):
        digest = b"b" * 64 + b"  checkpoint\n"
        with patch.object(backup, "_remote", side_effect=[digest, b""]):
            with self.assertRaises(FileExistsError):
                backup.plan("mini", "cluster", PurePosixPath("/a.ckpt"), PurePosixPath("/b.ckpt"))

    def test_copy_applies_permissions_and_verifies_destination(self):
        digest = b"c" * 64 + b"  checkpoint\n"
        with patch.object(backup, "_remote", side_effect=[b"", b"weights", b"", digest]) as remote:
            copied_hash = backup.copy("mini", "cluster", PurePosixPath("/source/ckpt"), PurePosixPath("/dest/ckpt"))
        self.assertEqual(copied_hash, "c" * 64)
        destination_write = remote.call_args_list[2]
        self.assertEqual(destination_write.kwargs["input_data"], b"weights")
        self.assertIn("chmod 600", destination_write.args[1])


if __name__ == "__main__":
    unittest.main()
