"""Correct Wordle feedback, including repeated-letter accounting."""

from collections import Counter
from typing_extensions import TypeAlias

Feedback = str
_VALID_MARKS = frozenset("GYB")
WORD_LENGTH = 5


def _validate_word(word: str, name: str) -> str:
    if not isinstance(word, str):
        raise TypeError(f"{name} must be a string")
    word = word.strip().lower()
    if len(word) != WORD_LENGTH or not word.isascii() or not word.isalpha():
        raise ValueError(f"{name} must contain exactly {WORD_LENGTH} ASCII letters")
    return word


def score_guess(guess: str, answer: str) -> Feedback:
    """Return a five-character pattern: G=green, Y=yellow, B=gray.

    Exact matches are allocated first. Yellow matches then consume only answer
    letter occurrences not already used by greens, matching standard Wordle.
    """
    guess = _validate_word(guess, "guess")
    answer = _validate_word(answer, "answer")
    marks = ["B"] * WORD_LENGTH
    remaining = Counter()

    # Pass 1: reserve exact-position matches and count unmatched answer letters.
    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            marks[i] = "G"
        else:
            remaining[a] += 1

    # Pass 2: allocate yellows from the remaining unmatched answer letters.
    for i, g in enumerate(guess):
        if marks[i] == "G":
            continue
        if remaining[g] > 0:
            marks[i] = "Y"
            remaining[g] -= 1

    return "".join(marks)


def validate_feedback(feedback: str) -> Feedback:
    """Normalize and validate a feedback pattern such as ``GYBBG``."""
    if not isinstance(feedback, str):
        raise TypeError("feedback must be a string")
    feedback = feedback.strip().upper()
    if len(feedback) != WORD_LENGTH or any(mark not in _VALID_MARKS for mark in feedback):
        raise ValueError("feedback must be exactly five characters using only G, Y, B")
    return feedback
