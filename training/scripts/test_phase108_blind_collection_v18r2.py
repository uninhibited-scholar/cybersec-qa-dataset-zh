from __future__ import annotations

import unittest

import torch

from phase108_blind_collection_v18r2 import RecentWindowRepetitionPenalty, visible_answer


class DummyTokenizer:
    def convert_tokens_to_ids(self, token):
        return {"<think>": 10, "</think>": 11}.get(token)

    def convert_ids_to_tokens(self, token_id):
        return {12: "<tool_call>"}.get(token_id, f"tok{token_id}")

    def decode(self, ids, skip_special_tokens=True):
        return "visible answer" if 20 in ids else ""


class BlindCollectionTests(unittest.TestCase):
    def test_repetition_penalty_uses_only_recent_generated_window(self):
        processor = RecentWindowRepetitionPenalty(prompt_length=2, window=1, penalty=1.12)
        input_ids = torch.tensor([[7, 8, 21, 22]])
        scores = torch.tensor([[0.0, -2.0, 2.0, 3.0, -4.0]])
        result = processor(input_ids, scores.clone())
        self.assertAlmostEqual(float(result[0, 22]), 2.0 / 1.12, places=5)
        self.assertAlmostEqual(float(result[0, 21]), 2.0, places=5)
        self.assertAlmostEqual(float(result[0, 8]), -2.0, places=5)

    def test_visible_answer_drops_thinking_and_flags_tool_marker(self):
        text, tool_marker, unclosed = visible_answer(DummyTokenizer(), torch.tensor([10, 30, 11, 20, 12]))
        self.assertEqual(text, "visible answer")
        self.assertTrue(tool_marker)
        self.assertFalse(unclosed)

    def test_unclosed_thinking_is_not_exposed_as_answer(self):
        text, tool_marker, unclosed = visible_answer(DummyTokenizer(), torch.tensor([10, 30]))
        self.assertEqual(text, "")
        self.assertFalse(tool_marker)
        self.assertTrue(unclosed)


if __name__ == "__main__":
    unittest.main()
