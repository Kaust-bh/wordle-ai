"""State management for a standard five-letter Wordle game."""

from typing import List, Set, Tuple

from .feedback import score_guess, validate_feedback


class GameState:
    """Manage guesses, feedback, and game termination."""

    def __init__(
        self,
        answer: str,
        allowed_guesses: List[str],
        max_guesses: int = 6,
    ) -> None:
        answer = answer.strip().lower()

        if len(answer) != 5 or not answer.isalpha() or not answer.isascii():
            raise ValueError("Answer must contain exactly five ASCII letters.")

        if max_guesses < 1:
            raise ValueError("max_guesses must be positive.")

        self.answer = answer
        self.allowed_guesses: Set[str] = {
            word.strip().lower() for word in allowed_guesses
        }
        self.max_guesses = max_guesses
        self.guesses: List[str] = []
        self.feedback_history: List[str] = []

    @property
    def won(self) -> bool:
        return bool(self.feedback_history) and self.feedback_history[-1] == "GGGGG"

    @property
    def game_over(self) -> bool:
        return self.won or len(self.guesses) >= self.max_guesses

    @property
    def remaining_turns(self) -> int:
        return self.max_guesses - len(self.guesses)

    def submit_guess(self, guess: str) -> Tuple[str, bool]:
        """Submit a legal guess and return (feedback, game_over)."""
        if self.game_over:
            raise ValueError("The game is already over.")

        guess = guess.strip().lower()

        if len(guess) != 5 or not guess.isalpha() or not guess.isascii():
            raise ValueError("Guess must contain exactly five ASCII letters.")

        if guess not in self.allowed_guesses:
            raise ValueError("Guess is not in the allowed-guess list.")

        feedback = score_guess(guess, self.answer)
        validate_feedback(feedback)

        self.guesses.append(guess)
        self.feedback_history.append(feedback)

        return feedback, self.game_over
