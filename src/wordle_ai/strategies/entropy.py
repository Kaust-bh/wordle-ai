
"""Information-theoretic Wordle guess ranking."""

from collections import Counter
from dataclasses import dataclass
import math

import numpy as np

from ..feedback import score_guess


@dataclass(frozen=True)
class EntropyResult:
    guess: str
    entropy: float
    solve_probability: float
    expected_remaining: float
    worst_case_remaining: int


def score_guess_information(guess, candidates):
    """Calculate information metrics for one guess."""
    candidates = list(candidates)

    if not candidates:
        raise ValueError("Candidates cannot be empty")

    counts = Counter(
        score_guess(guess, answer)
        for answer in candidates
    )
    total = len(candidates)

    entropy = -sum(
        (count / total) * math.log2(count / total)
        for count in counts.values()
    )

    expected_remaining = sum(
        count * count for count in counts.values()
    ) / total

    return EntropyResult(
        guess=guess,
        entropy=entropy,
        solve_probability=sum(
            answer == guess for answer in candidates
        ) / total,
        expected_remaining=expected_remaining,
        worst_case_remaining=max(counts.values()),
    )


def rank_guesses(legal_guesses, candidates, top_k=10, matrix=None):
    """Rank guesses by descending entropy.

    If a precomputed FeedbackMatrix is supplied, use NumPy to
    calculate feedback bucket statistics efficiently.
    """
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    legal_guesses = list(legal_guesses)
    candidates = list(candidates)

    if not candidates:
        raise ValueError("Candidates cannot be empty")

    if not legal_guesses:
        raise ValueError("Legal guesses cannot be empty")

    # When only a few answers remain, guessing an answer directly
    # is preferable to using a probe word.
    if len(candidates) <= 2:
        candidate_set = set(candidates)
        candidate_guesses = [
            guess for guess in legal_guesses
            if guess in candidate_set
        ]
        if candidate_guesses:
            legal_guesses = candidate_guesses

    total = len(candidates)
    candidate_set = set(candidates)

    # Reference implementation, also used when no matrix is provided.
    if matrix is None:
        results = [
            score_guess_information(guess, candidates)
            for guess in legal_guesses
        ]
        return sorted(
            results,
            key=lambda item: (-item.entropy, item.guess),
        )[:top_k]

    # Vectorized path using the precomputed feedback matrix.
    candidate_indices = np.fromiter(
        (matrix.answer_index[word] for word in candidates),
        dtype=np.int64,
        count=total,
    )

    guess_indices = np.fromiter(
        (matrix.guess_index[guess] for guess in legal_guesses),
        dtype=np.int64,
        count=len(legal_guesses),
    )

    codes = matrix.rows[np.ix_(guess_indices, candidate_indices)]

    number_of_guesses = len(legal_guesses)

    # Each guess gets its own range of 243 possible feedback patterns.
    offsets = (
        np.arange(number_of_guesses, dtype=np.int64)[:, None] * 243
    )
    combined = (codes.astype(np.int64) + offsets).ravel()

    counts = np.bincount(
        combined,
        minlength=number_of_guesses * 243,
    ).reshape(number_of_guesses, 243)

    probabilities = counts / total

    with np.errstate(divide="ignore", invalid="ignore"):
        terms = np.where(
            probabilities > 0,
            probabilities * np.log2(
                np.maximum(probabilities, 1e-300)
            ),
            0.0,
        )

    entropies = -terms.sum(axis=1)

    expected_remaining = (
        counts.astype(np.float64) ** 2
    ).sum(axis=1) / total

    worst_case_remaining = counts.max(axis=1)

    results = [
        EntropyResult(
            guess=guess,
            entropy=float(entropies[i]),
            solve_probability=(
                1.0 / total if guess in candidate_set else 0.0
            ),
            expected_remaining=float(expected_remaining[i]),
            worst_case_remaining=int(worst_case_remaining[i]),
        )
        for i, guess in enumerate(legal_guesses)
    ]

    return sorted(
        results,
        key=lambda item: (-item.entropy, item.guess),
    )[:top_k]
