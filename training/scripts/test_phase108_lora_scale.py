import unittest

from training.scripts.phase108_scale_utils import mlx_scale_to_peft_alpha


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


if __name__ == "__main__":
    unittest.main()
