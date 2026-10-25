
"""Vectorized minimax Wordle guess ranking."""

from collections import Counter
from dataclasses import dataclass

import numpy as np

from ..feedback import score_guess


PATTERN_COUNT = 243
DEFAULT_BATCH_SIZE = 512


@dataclass(frozen=True)
class MinimaxResult:
    guess: str
    worst_case_remaining: int
    expected_remaining: float
    solve_probability: float


def score_guess_minimax(guess, candidates, matrix=None):
    """Score one guess by its worst-case candidate group."""
    candidates = list(candidates)

    if not candidates:
        raise ValueError("Candidates cannot be empty")

    if matrix is None:
        counts = Counter(
            score_guess(guess, answer) for answer in candidates
        )
        group_sizes = list(counts.values())
    else:
        codes = matrix.candidate_codes(guess, candidates)
        counts = np.bincount(codes, minlength=PATTERN_COUNT)
        group_sizes = counts[counts > 0].tolist()

    total = len(candidates)

    return MinimaxResult(
        guess=guess,
        worst_case_remaining=max(group_sizes),
        expected_remaining=sum(n * n for n in group_sizes) / total,
        solve_probability=1.0 / total if guess in set(candidates) else 0.0,
    )


def rank_minimax(
    legal_guesses,
    candidates,
    top_k=10,
    matrix=None,
    batch_size=DEFAULT_BATCH_SIZE,
):
    """Rank guesses by worst-case group, using vectorized batches."""
    legal_guesses = list(legal_guesses)
    candidates = list(candidates)

    if top_k <= 0:
        raise ValueError("top_k must be positive")
    if not candidates:
        raise ValueError("Candidates cannot be empty")
    if not legal_guesses:
        raise ValueError("Legal guesses cannot be empty")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    candidate_set = set(candidates)

    # With one or two answers remaining, prefer a possible answer.
    if len(candidates) <= 2:
        candidate_guesses = [
            guess for guess in legal_guesses
            if guess in candidate_set
        ]
        if candidate_guesses:
            legal_guesses = candidate_guesses

    total = len(candidates)
    number_of_guesses = len(legal_guesses)

    # Fallback for calls that do not supply a feedback matrix.
    if matrix is None:
        results = [
            score_guess_minimax(guess, candidates)
            for guess in legal_guesses
        ]
        return sorted(
            results,
            key=lambda result: (
                result.worst_case_remaining,
                -result.solve_probability,
                result.expected_remaining,
                result.guess,
            ),
        )[:top_k]

    # Convert candidate words to matrix column indices once.
    candidate_indices = np.fromiter(
        (matrix.answer_index[word] for word in candidates),
        dtype=np.int64,
        count=total,
    )
    guess_indices = np.fromiter(
        (matrix.guess_index[guess] for guess in legal_guesses),
        dtype=np.int64,
        count=number_of_guesses,
    )

    worst_cases = np.empty(number_of_guesses, dtype=np.int64)
    expected_remaining = np.empty(number_of_guesses, dtype=np.float64)

    # Batch guesses to limit temporary memory usage.
    for start in range(0, number_of_guesses, batch_size):
        end = min(start + batch_size, number_of_guesses)
        batch_indices = guess_indices[start:end]
        batch_count = end - start

        codes = matrix.rows[np.ix_(batch_indices, candidate_indices)]

        # Give each guess its own range of 243 histogram bins.
        offsets = (
            np.arange(batch_count, dtype=np.int64)[:, None]
            * PATTERN_COUNT
        )
        combined = (codes.astype(np.int64) + offsets).ravel()

        counts = np.bincount(
            combined,
            minlength=batch_count * PATTERN_COUNT,
        ).reshape(batch_count, PATTERN_COUNT)

        worst_cases[start:end] = counts.max(axis=1)
        expected_remaining[start:end] = (
            counts.astype(np.float64) ** 2
        ).sum(axis=1) / total

    results = [
        MinimaxResult(
            guess=guess,
            worst_case_remaining=int(worst_cases[i]),
            expected_remaining=float(expected_remaining[i]),
            solve_probability=(
                1.0 / total if guess in candidate_set else 0.0
            ),
        )
        for i, guess in enumerate(legal_guesses)
    ]

    return sorted(
        results,
        key=lambda result: (
            result.worst_case_remaining,
            -result.solve_probability,
            result.expected_remaining,
            result.guess,
        ),
    )[:top_k]
