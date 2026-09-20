import unittest

import torch

from phase108_hf_adapter_smoke import LoRAProjection


class LoRAProjectionTest(unittest.TestCase):
    def test_mlx_factor_orientation_and_scale(self):
        torch.manual_seed(108)
        base = torch.nn.Linear(5, 7, bias=False, dtype=torch.float64)
        x = torch.randn(2, 3, 5, dtype=torch.float64)
        mlx_a = torch.randn(5, 2, dtype=torch.float64)
        mlx_b = torch.randn(2, 7, dtype=torch.float64)
        scale = 20.0

        wrapped = LoRAProjection(base, mlx_a.T.contiguous(), mlx_b.T.contiguous(), scale)
        actual = wrapped(x)
        expected = base(x) + scale * ((x @ mlx_a) @ mlx_b)
        torch.testing.assert_close(actual, expected, rtol=1e-12, atol=1e-12)

    def test_base_path_preserved_when_adapter_is_zero(self):
        base = torch.nn.Linear(4, 4, bias=True, dtype=torch.float64)
        x = torch.randn(2, 4, dtype=torch.float64)
        wrapped = LoRAProjection(base, torch.zeros(2, 4, dtype=torch.float64),
                                 torch.randn(4, 2, dtype=torch.float64), 20.0)
        torch.testing.assert_close(wrapped(x), base(x), rtol=0, atol=0)


if __name__ == "__main__":
    unittest.main()
