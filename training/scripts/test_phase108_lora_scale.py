import unittest

from training.scripts.phase108_scale_utils import (
    canonical_mlx_lora_key,
    mlx_key_to_peft_state_key,
    mlx_scale_to_peft_alpha,
)


class MlxPeftScaleTest(unittest.TestCase):
    def test_mlx_direct_scale_matches_peft_effective_scale(self):
        rank = 8
        alpha = mlx_scale_to_peft_alpha(20.0, rank)
        self.assertEqual(alpha, 160.0)
        self.assertEqual(alpha / rank, 20.0)

    def test_invalid_scale_or_rank_is_rejected(self):
        with self.assertRaises(ValueError):
            mlx_scale_to_peft_alpha(0.0, 8)
        with self.assertRaises(ValueError):
            mlx_scale_to_peft_alpha(20.0, 0)
        with self.assertRaises(ValueError):
            mlx_scale_to_peft_alpha(float("inf"), 8)
        with self.assertRaises(ValueError):
            mlx_scale_to_peft_alpha(20.0, True)

    def test_mlx_adapter_key_prefixes_are_normalized(self):
        self.assertEqual(
            canonical_mlx_lora_key("layers.32.mlp.down_proj.lora_a"),
            ("model.layers.32.mlp.down_proj", 32, "a"),
        )
        self.assertEqual(
            canonical_mlx_lora_key("model.layers.35.self_attn.q_proj.lora_b"),
            ("model.layers.35.self_attn.q_proj", 35, "b"),
        )
        self.assertEqual(
            mlx_key_to_peft_state_key("layers.32.mlp.down_proj.lora_a"),
            "base_model.model.model.layers.32.mlp.down_proj.lora_A.default.weight",
        )
        with self.assertRaises(ValueError):
            canonical_mlx_lora_key("something.layers.32.mlp.down_proj.lora_a")


if __name__ == "__main__":
    unittest.main()
