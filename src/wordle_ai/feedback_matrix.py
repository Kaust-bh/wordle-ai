
"""Compact, reusable feedback matrix with disk caching."""

import hashlib
from pathlib import Path

import numpy as np

from .feedback import score_guess

SYMBOL = {"B": 0, "Y": 1, "G": 2}


def encode_feedback(pattern):
    value = 0
    for char in pattern:
        value = value * 3 + SYMBOL[char]
    return value


class FeedbackMatrix:
    """Store feedback codes for every guess-answer pair."""

    def __init__(self, answers, guesses):
        self.answers = list(answers)
        self.guesses = list(guesses)
        self.answer_index = {word: i for i, word in enumerate(self.answers)}
        self.guess_index = {word: i for i, word in enumerate(self.guesses)}
        self.rows = None

    def _cache_path(self, cache_dir="data/cache"):
        """Create a cache filename tied to the exact word lists."""
        digest = hashlib.sha256()
        for word in self.answers:
            digest.update(word.encode("ascii"))
            digest.update(b"\n")
        digest.update(b"--GUESSES--\n")
        for word in self.guesses:
            digest.update(word.encode("ascii"))
            digest.update(b"\n")

        return Path(cache_dir) / ("feedback_" + digest.hexdigest()[:20] + ".npy")

    def build(self, cache_dir="data/cache"):
        """Load the cached matrix or build and save it."""
        cache_path = self._cache_path(cache_dir)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        if cache_path.exists():
            print("Loading cached feedback matrix:", cache_path, flush=True)
            self.rows = np.load(str(cache_path), mmap_mode="r")
            expected_shape = (len(self.guesses), len(self.answers))
            if self.rows.shape == expected_shape and self.rows.dtype == np.uint8:
                print("Cached matrix loaded.", flush=True)
                return
            print("Cache shape or dtype mismatch. Rebuilding.", flush=True)

        total_guesses = len(self.guesses)
        total_answers = len(self.answers)
        matrix = np.empty(
            (total_guesses, total_answers), dtype=np.uint8
        )

        for i, guess in enumerate(self.guesses):
            matrix[i, :] = np.fromiter(
                (
                    encode_feedback(score_guess(guess, answer))
                    for answer in self.answers
                ),
                dtype=np.uint8,
                count=total_answers,
            )

            if (i + 1) % 1000 == 0 or i + 1 == total_guesses:
                print(
                    "Precomputed {}/{} guesses".format(
                        i + 1, total_guesses
                    ),
                    flush=True,
                )

        np.save(str(cache_path), matrix)
        self.rows = matrix
        print("Saved feedback matrix cache:", cache_path, flush=True)

    def pattern(self, guess, answer):
        return int(
            self.rows[
                self.guess_index[guess],
                self.answer_index[answer],
            ]
        )

    def candidate_codes(self, guess, candidates):
        indices = np.fromiter(
            (self.answer_index[word] for word in candidates),
            dtype=np.int64,
            count=len(candidates),
        )
        return self.rows[self.guess_index[guess], indices]
