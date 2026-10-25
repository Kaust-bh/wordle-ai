
import pytest

from wordle_ai.strategies.minimax import (
    rank_minimax,
    score_guess_minimax,
)


def test_minimax_scores_worst_case_correctly():
    candidates = ["aaaaa", "bbbbb", "ccccc", "ddddd"]

    result = score_guess_minimax("aaaaa", candidates)

    assert result.worst_case_remaining == 3
    assert result.expected_remaining == 2.5
    assert result.solve_probability == 0.25


def test_minimax_returns_sorted_results():
    candidates = ["aaaaa", "bbbbb", "ccccc"]
    guesses = ["aaaaa", "bbbbb", "ccccc"]

    results = rank_minimax(guesses, candidates, top_k=3)

    assert len(results) == 3

    scores = [r.worst_case_remaining for r in results]
    assert scores == sorted(scores)


def test_minimax_rejects_empty_candidates():
    with pytest.raises(ValueError):
        score_guess_minimax("crane", [])


def test_minimax_rejects_invalid_top_k():
    with pytest.raises(ValueError):
        rank_minimax(["crane"], ["crane"], top_k=0)
