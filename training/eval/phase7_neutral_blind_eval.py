#!/usr/bin/env python3
"""Compare Phase 7 checkpoints against the strongest previous candidate."""

from pathlib import Path

import phase6_neutral_blind_eval as suite


HOME = Path.home()
suite.base.OUT = HOME / "cyber-agent/phase7-neutral-blind-eval"
suite.base.SEED = 20260904
suite.base.CANDIDATES = {
    "phase5_step120": (
        HOME / "models/qwen-cyber-adapter-phase5-corrective/0000120_adapters.safetensors"
    ),
    "phase7_step80": (
        HOME / "models/qwen-cyber-adapter-phase7-provenance-refine/0000080_adapters.safetensors"
    ),
    "phase7_step220": (
        HOME / "models/qwen-cyber-adapter-phase7-provenance-refine/0000220_adapters.safetensors"
    ),
}


if __name__ == "__main__":
    suite.base.main()
