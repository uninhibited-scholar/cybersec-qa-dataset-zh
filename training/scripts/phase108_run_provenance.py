"""Hash and describe the immutable inputs of a Phase108 training run."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def model_weight_files(base: Path) -> list[Path]:
    """Resolve the exact safetensors shards listed by the HF weight index."""
    index = base / "model.safetensors.index.json"
    if not index.is_file():
        raise FileNotFoundError(f"missing model weight index: {index}")
    data = json.loads(index.read_text(encoding="utf-8"))
    raw_names = list(data.get("weight_map", {}).values())
    if not raw_names or not all(isinstance(name, str) for name in raw_names):
        raise ValueError(f"invalid or empty weight_map in {index}")
    names = sorted(set(raw_names))
    paths = [base / name for name in names]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing model shards: " + ", ".join(missing))
    return paths


def model_files_manifest(base: Path) -> dict[str, Any]:
    """Hash model config, index, every indexed weight shard, and tokenizer files."""
    base = base.resolve()
    config = base / "config.json"
    if not config.is_file():
        raise FileNotFoundError(f"missing model config: {config}")
    files: dict[str, str] = {
        "config.json": sha256_file(config),
        "model.safetensors.index.json": sha256_file(base / "model.safetensors.index.json"),
    }
    for path in model_weight_files(base):
        files[str(path.relative_to(base))] = sha256_file(path)
    tokenizer_names = (
        "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
        "added_tokens.json", "vocab.json", "merges.txt", "tokenizer.model",
        "spiece.model", "chat_template.jinja",
    )
    for name in tokenizer_names:
        path = base / name
        if path.is_file():
            files[name] = sha256_file(path)
    return {"path": str(base), "files_sha256": files}


def stable_file_manifest(path: Path) -> dict[str, Any]:
    """Capture a file fingerprint and reject a file that changes during hashing."""
    path = path.resolve()
    before = path.stat()
    digest = sha256_file(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (
        after.st_size, after.st_mtime_ns, after.st_ino
    ):
        raise RuntimeError(f"input changed while hashing: {path}")
    return {"path": str(path), "bytes": before.st_size, "sha256": digest}
