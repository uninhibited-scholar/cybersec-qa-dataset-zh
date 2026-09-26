import json
import tempfile
import unittest
from pathlib import Path

from training.scripts.phase108_run_provenance import (
    model_files_manifest,
    sha256_file,
    stable_file_manifest,
)


class Phase108RunProvenanceTest(unittest.TestCase):
    def test_model_manifest_pins_config_index_shards_and_tokenizer(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            (base / "config.json").write_text('{"model_type":"test"}\n')
            (base / "model-00001.safetensors").write_bytes(b"weights-a")
            (base / "model-00002.safetensors").write_bytes(b"weights-b")
            (base / "model.safetensors.index.json").write_text(json.dumps({
                "weight_map": {"a": "model-00001.safetensors", "b": "model-00002.safetensors"}
            }))
            (base / "tokenizer_config.json").write_text('{"chat_template":"test"}\n')

            manifest = model_files_manifest(base)

            self.assertEqual(
                manifest["files_sha256"]["model-00001.safetensors"],
                sha256_file(base / "model-00001.safetensors"),
            )
            self.assertEqual(
                manifest["files_sha256"]["model-00002.safetensors"],
                sha256_file(base / "model-00002.safetensors"),
            )
            self.assertIn("tokenizer_config.json", manifest["files_sha256"])
            self.assertIn("config.json", manifest["files_sha256"])
            self.assertIn("model.safetensors.index.json", manifest["files_sha256"])

    def test_missing_weight_shard_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            (base / "config.json").write_text("{}\n")
            (base / "model.safetensors.index.json").write_text(json.dumps({
                "weight_map": {"a": "missing.safetensors"}
            }))
            with self.assertRaises(FileNotFoundError):
                model_files_manifest(base)

    def test_stable_file_manifest_records_path_size_and_hash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "input.jsonl"
            path.write_bytes(b'{"prompt":"x","completion":"y"}\n')
            manifest = stable_file_manifest(path)
            self.assertEqual(manifest["path"], str(path.resolve()))
            self.assertEqual(manifest["bytes"], path.stat().st_size)
            self.assertEqual(manifest["sha256"], sha256_file(path))


if __name__ == "__main__":
    unittest.main()
