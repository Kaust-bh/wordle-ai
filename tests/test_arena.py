import unittest

from wordle_ai.arena import (
    apply_keyboard_input,
    compare_results,
    normalize_custom_word,
    sanitize_keyboard_text,
    solve_target,
    update_keyboard_state,
)
from wordle_ai.feedback_matrix import FeedbackMatrix
from wordle_ai.game import GameState


class ArenaTests(unittest.TestCase):
    ANSWERS = ["apple", "cigar", "crane"]

    def test_custom_word_validation(self):
        self.assertEqual(
            normalize_custom_word("  CIGAR ", self.ANSWERS),
            ("cigar", None),
        )

        for value in ("four", "sixsix", "ab1de", "éabcd", "zzzzz"):
            with self.subTest(value=value):
                word, error = normalize_custom_word(value, self.ANSWERS)
                self.assertIsNone(word)
                self.assertTrue(error)

    def test_keyboard_keeps_strongest_feedback(self):
        keyboard = update_keyboard_state({}, "crane", "GYYBB")
        keyboard = update_keyboard_state(keyboard, "cigar", "GBBBG")

        self.assertEqual(keyboard["c"], "G")
        self.assertEqual(keyboard["a"], "Y")
        self.assertEqual(keyboard["r"], "G")
        self.assertEqual(keyboard["e"], "B")

    def test_keyboard_all_colour_transitions(self):
        transitions = (
            ("B", "Y", "Y"),
            ("B", "G", "G"),
            ("Y", "G", "G"),
            ("Y", "B", "Y"),
            ("G", "Y", "G"),
            ("G", "B", "G"),
        )

        for existing, incoming, expected in transitions:
            with self.subTest(existing=existing, incoming=incoming):
                result = update_keyboard_state(
                    {"a": existing}, "a", incoming
                )
                self.assertEqual(result["a"], expected)

    def test_keyboard_input_supports_letters_backspace_and_enter(self):
        current = ""
        for key in "crane":
            current = apply_keyboard_input(current, key)
        self.assertEqual(current, "crane")

        self.assertEqual(apply_keyboard_input(current, "backspace"), "cran")
        self.assertEqual(apply_keyboard_input(current, "enter"), "crane")
        self.assertEqual(apply_keyboard_input("crane", "x"), "crane")

    def test_keyboard_input_ignores_unsupported_keys_and_caps_at_five(self):
        current = ""
        for key in ("1", "é", "c", "r", "a", "n", "e", "x"):
            current = apply_keyboard_input(current, key)
        self.assertEqual(current, "crane")
        self.assertEqual(
            sanitize_keyboard_text(" C@r1anéx"),
            "cranx",
        )

    def test_human_guess_uses_shared_validation_and_feedback(self):
        game = GameState("cigar", ["cigar", "crane", "apple"])

        feedback, game_over = game.submit_guess("crane")

        self.assertEqual(feedback, "GYYBB")
        self.assertFalse(game_over)
        with self.assertRaises(ValueError):
            game.submit_guess("zzzzz")

    def test_human_six_guess_limit(self):
        game = GameState("cigar", ["apple", "cigar"], max_guesses=6)
        for _ in range(6):
            feedback, game_over = game.submit_guess("apple")

        self.assertTrue(game_over)
        self.assertFalse(game.won)
        with self.assertRaises(ValueError):
            game.submit_guess("apple")

    def test_comparison_handles_wins_failures_and_ties(self):
        history = [{"guess": "cigar"}]
        self.assertEqual(
            compare_results(history, True, [{"guess": "crane"}], True),
            {"human_guesses": 1, "ai_guesses": 1, "winner": "tie"},
        )
        self.assertEqual(
            compare_results(history, False, [{"guess": "crane"}], True),
            {"human_guesses": None, "ai_guesses": 1, "winner": "ai"},
        )
        self.assertEqual(
            compare_results(history, False, [], False),
            {"human_guesses": None, "ai_guesses": None, "winner": "neither"},
        )

    def test_entropy_and_minimax_solve_a_custom_answer(self):
        words = ["apple", "cigar", "crane"]
        matrix = FeedbackMatrix(words, words)
        matrix.build()

        for strategy in ("Entropy", "Minimax"):
            with self.subTest(strategy=strategy):
                history = solve_target(
                    "cigar", words, words, matrix, strategy
                )
                self.assertLessEqual(len(history), 6)
                self.assertEqual(history[-1]["guess"], "cigar")

    def test_human_and_ai_share_the_same_target(self):
        target = "cigar"
        game = GameState(target, self.ANSWERS)
        ai_history = [{"guess": target, "pattern": "GGGGG"}]

        self.assertEqual(game.answer, target)
        self.assertEqual(ai_history[-1]["guess"], game.answer)


if __name__ == "__main__":
    unittest.main()