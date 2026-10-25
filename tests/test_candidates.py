import unittest

from wordle_ai.candidates import assert_history_consistent, filter_candidates, validate_history
from wordle_ai.feedback import score_guess


class CandidateTests(unittest.TestCase):
    def test_filter_candidates(self):
        words = ["crane", "cigar", "caper", "slate"]
        expected = [w for w in words if score_guess("crane", w) == "GYYBB"]
        self.assertEqual(filter_candidates(words, "crane", "GYYBB"), expected)

    def test_history_applies_all_turns(self):
        words = ["crane", "cigar", "caper", "slate", "share"]
        history = [("crane", "BBBBB"), ("slate", "BBBBB")]
        expected = [w for w in words if all(score_guess(g, w) == f for g, f in history)]
        self.assertEqual(validate_history(words, history), expected)

    def test_contradictory_history_raises(self):
        with self.assertRaisesRegex(ValueError, "No candidates match"):
            assert_history_consistent(["crane", "cigar"], [("crane", "GGGGG"), ("cigar", "BBBBB")])

    def test_invalid_feedback_rejected(self):
        with self.assertRaises(ValueError):
            filter_candidates(["crane"], "crane", "GGGGX")


if __name__ == "__main__":
    unittest.main()
