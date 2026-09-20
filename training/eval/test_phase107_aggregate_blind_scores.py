import unittest

from phase107_aggregate_blind_scores import (
    bootstrap_differences,
    expected_index,
    percentile,
    validate,
)


class Phase107AggregateTests(unittest.TestCase):
    def test_percentile_interpolates(self):
        self.assertEqual(percentile([0.0, 10.0], 0.25), 2.5)

    def test_expected_index_requires_three_aliases_per_case(self):
        bundle = [
            {
                "case_id": "case-1",
                "responses": [
                    {"blind_alias": alias} for alias in ("A", "B", "C")
                ],
            }
        ]
        with self.assertRaisesRegex(ValueError, "exactly 320 cases"):
            expected_index(bundle)

    def test_validation_rejects_scoring_an_empty_response(self):
        key = (1, "case-1", "A")
        expected = {key: ({}, {"classification": "empty"})}
        review = {key: {"response_state": "empty", "scores": [0, 0, 0, 0]}}
        with self.assertRaisesRegex(ValueError, "empty response was scored"):
            validate(review, expected, "A")

    def test_bootstrap_is_deterministic_and_paired_by_case(self):
        scores = {
            "one": {
                "A": {"c1": 8.0, "c2": 6.0},
                "B": {"c1": 6.0, "c2": 6.0, "c3": 8.0},
            }
        }
        first = bootstrap_differences(scores, ["A", "B"], ["one"], 200, 7)
        second = bootstrap_differences(scores, ["A", "B"], ["one"], 200, 7)
        self.assertEqual(first, second)
        self.assertEqual(first["A-minus-B"]["paired_case_n"], 2)
        self.assertEqual(first["A-minus-B"]["case_weighted_mean_difference"], 1.0)


if __name__ == "__main__":
    unittest.main()
