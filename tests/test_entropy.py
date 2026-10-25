import unittest

from wordle_ai.strategies.entropy import (
    rank_guesses,
    score_guess_information,
)


class TestEntropy(unittest.TestCase):
    def test_entropy_is_zero_when_feedback_is_identical(self):
        result = score_guess_information("zzzzz", ["apple", "ample"])
        self.assertAlmostEqual(result.entropy, 0.0)
        self.assertEqual(result.expected_remaining, 2.0)
        self.assertEqual(result.worst_case_remaining, 2)

    def test_entropy_is_one_for_two_distinct_patterns(self):
        result = score_guess_information("apple", ["apple", "ample"])
        self.assertAlmostEqual(result.entropy, 1.0)
        self.assertEqual(result.expected_remaining, 1.0)
        self.assertEqual(result.worst_case_remaining, 1)

    def test_candidate_guess_has_solve_probability(self):
        result = score_guess_information("apple", ["apple", "ample"])
        self.assertAlmostEqual(result.solve_probability, 0.5)

    def test_probe_has_zero_solve_probability(self):
        result = score_guess_information("zzzzz", ["apple", "ample"])
        self.assertEqual(result.solve_probability, 0.0)

    def test_ranking_is_deterministic(self):
        guesses = ["crane", "apple", "ample"]
        candidates = ["apple", "ample"]
        self.assertEqual(
            rank_guesses(guesses, candidates, 3),
            rank_guesses(guesses, candidates, 3),
        )

    def test_small_candidate_set_prioritizes_answers(self):
        result = rank_guesses(
            ["crane", "apple", "ample"], ["apple", "ample"], 5
        )
        self.assertEqual(
            {item.guess for item in result}, {"apple", "ample"}
        )

    def test_empty_candidates_rejected(self):
           with self.assertRaises(ValueError):
            rank_guesses(["crane"], ["apple"], top_k=0)


if __name__ == "__main__":
    unittest.main()
