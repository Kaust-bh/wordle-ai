import unittest

from wordle_ai.feedback import score_guess, validate_feedback


class FeedbackTests(unittest.TestCase):
    def test_all_green(self):
        self.assertEqual(score_guess("crane", "crane"), "GGGGG")

    def test_all_gray(self):
        self.assertEqual(score_guess("fjord", "apple"), "BBBBB")

    def test_basic_mixed_pattern(self):
        self.assertEqual(score_guess("crane", "cigar"), "GYYBB")

    def test_duplicate_guess_only_one_answer_occurrence(self):
        # The green A is reserved first; only one unmatched A remains for a yellow.
        self.assertEqual(score_guess("array", "cacao"), "YBBGB")

    def test_duplicate_guess_limited_yellows(self):
        # Duplicate Ls are limited by the answer; exact matches are reserved first.
        self.assertEqual(score_guess("allee", "label"), "YYYGB")

    def test_green_is_reserved_before_yellow(self):
        self.assertEqual(score_guess("sassy", "assay"), "YYGBG")

    def test_repeated_answer_letters(self):
        self.assertEqual(score_guess("eerie", "serve"), "BGGBG")

    def test_case_normalization(self):
        self.assertEqual(score_guess("CRANE", "crane"), "GGGGG")

    def test_invalid_word(self):
        for word in ("four", "sixsix", "ab1de", "éabcd"):
            with self.subTest(word=word), self.assertRaises(ValueError):
                score_guess(word, "crane")

    def test_feedback_validation(self):
        self.assertEqual(validate_feedback(" gybbg "), "GYBBG")
        for pattern in ("GGGG", "GGGGGG", "GGXBB", "12345"):
            with self.subTest(pattern=pattern), self.assertRaises(ValueError):
                validate_feedback(pattern)


if __name__ == "__main__":
    unittest.main()
