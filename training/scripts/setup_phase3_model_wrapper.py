#!/usr/bin/env python3
"""Create a lightweight model view with a raw-concatenation training template."""

import json
import os
from pathlib import Path

home = Path.home()
source = home / "models/Qwen3-4B-mlx-4bit"
target = home / "models/Qwen3-4B-mlx-4bit-phase3-wrapper"
target.mkdir(parents=True, exist_ok=True)

for item in source.iterdir():
    destination = target / item.name
    if item.name == "tokenizer_config.json":
        config = json.loads(item.read_text(encoding="utf-8"))
        config["chat_template"] = (
            "{% for message in messages %}{{ message['content'] }}"
            "{% if message['role'] == 'assistant' %}{{ eos_token }}{% endif %}"
            "{% endfor %}"
        )
        destination.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    elif not destination.exists():
        os.symlink(item, destination)

print(target)
