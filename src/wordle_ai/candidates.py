"""Candidate filtering and history consistency checks."""

from collections.abc import Iterable, Sequence

from .feedback import Feedback, score_guess, validate_feedback


def filter_candidates(candidates: Iterable[str], guess: str, feedback: Feedback) -> list[str]:
    """Keep candidates that produce exactly the observed feedback."""
    feedback = validate_feedback(feedback)
    return [word for word in candidates if score_guess(guess, word) == feedback]


def validate_history(candidates: Iterable[str], history: Sequence[tuple[str, Feedback]]) -> list[str]:
    """Filter candidates against every (guess, feedback) pair in history."""
    remaining = list(candidates)
    for guess, feedback in history:
        remaining = filter_candidates(remaining, guess, feedback)
        if not remaining:
            break
    return remaining


def assert_history_consistent(candidates: Iterable[str], history: Sequence[tuple[str, Feedback]]) -> list[str]:
    """Return consistent candidates, raising a helpful error if none remain."""
    result = validate_history(candidates, history)
    if not result:
        raise ValueError(
            "No candidates match the supplied feedback history. Check for a mistyped "
            "guess/feedback pattern, an answer missing from the word list, or a bug."
        )
    return result
