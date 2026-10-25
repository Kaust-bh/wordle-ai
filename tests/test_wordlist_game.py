import tempfile
import unittest
from pathlib import Path

from wordle_ai.game import GameState
from wordle_ai.wordlist import load_word_list


class TestWordList(unittest.TestCase):
    def test_load_normalizes_and_removes_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "words.txt"
            path.write_text(
                "# test words\nCRANE\nslate\ncrane\n\n",
                encoding="utf-8",
            )
            self.assertEqual(
                load_word_list(str(path)),
                ["crane", "slate"],
            )

    def test_invalid_word_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "words.txt"
            path.write_text("crane\nabc\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_word_list(str(path))

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            load_word_list("/definitely/missing/wordlist.txt")


class TestGameState(unittest.TestCase):
    def setUp(self):
        self.game = GameState("apple", ["apple", "ample", "crane"])

    def test_correct_guess_wins(self):
        feedback, over = self.game.submit_guess("APPLE")
        self.assertEqual(feedback, "GGGGG")
        self.assertTrue(over)
        self.assertTrue(self.game.won)

    def test_wrong_guess_continues(self):
        feedback, over = self.game.submit_guess("crane")
        self.assertEqual(len(feedback), 5)
        self.assertFalse(over)
        self.assertEqual(self.game.remaining_turns, 5)

    def test_illegal_guess_does_not_consume_turn(self):
        with self.assertRaises(ValueError):
            self.game.submit_guess("zzzzz")
        self.assertEqual(len(self.game.guesses), 0)

    def test_game_stops_after_six_guesses(self):
        game = GameState("apple", ["crane"], max_guesses=2)
        game.submit_guess("crane")
        _, over = game.submit_guess("crane")
        self.assertTrue(over)
        self.assertFalse(game.won)

        with self.assertRaises(ValueError):
            game.submit_guess("crane")

    def test_no_guess_after_winning(self):
        self.game.submit_guess("apple")
        with self.assertRaises(ValueError):
            self.game.submit_guess("crane")


if __name__ == "__main__":
    unittest.main()
