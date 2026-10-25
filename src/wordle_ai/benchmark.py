
"""Benchmark Wordle strategies against a fixed answer set."""

import argparse
import json
import time
from collections import Counter
from pathlib import Path

from .feedback_matrix import FeedbackMatrix, encode_feedback
from .strategies.entropy import rank_guesses
from .strategies.minimax import rank_minimax
from .wordlist import load_word_list


MAX_ATTEMPTS = 6
WIN_CODE = encode_feedback("GGGGG")


def choose_guess(strategy, legal_guesses, candidates, matrix):
    """Choose the next guess using the requested strategy."""
    if strategy == "entropy":
        ranked = rank_guesses(
            legal_guesses, candidates, top_k=1, matrix=matrix
        )
    elif strategy == "minimax":
        ranked = rank_minimax(
            legal_guesses, candidates, top_k=1, matrix=matrix
        )
    else:
        raise ValueError("Unknown strategy: {}".format(strategy))

    return ranked[0].guess


def simulate_game(secret, answers, legal_guesses, matrix,
                  strategy, max_attempts=MAX_ATTEMPTS):
    """Simulate one game and return its result."""
    candidates = list(answers)
    history = []

    for attempt in range(1, max_attempts + 1):
        guess = choose_guess(
            strategy, legal_guesses, candidates, matrix
        )

        feedback = matrix.pattern(guess, secret)
        history.append(guess)

        if feedback == WIN_CODE:
            return {
                "solved": True,
                "guesses": attempt,
                "history": history,
            }

        # Keep only answers consistent with the observed feedback.
        codes = matrix.candidate_codes(guess, candidates)
        candidates = [
            word
            for word, code in zip(candidates, codes)
            if int(code) == feedback
        ]

        if not candidates:
            break

    return {
        "solved": False,
        "guesses": len(history),
        "history": history,
    }


def benchmark_strategy(strategy, answers, legal_guesses, matrix):
    """Evaluate a strategy against every supplied secret answer."""
    started = time.perf_counter()

    solved_counts = []
    all_counts = []
    failures = 0
    distribution = Counter()
    total_game_seconds = 0.0

    for index, secret in enumerate(answers, start=1):
        game_started = time.perf_counter()

        result = simulate_game(
            secret=secret,
            answers=answers,
            legal_guesses=legal_guesses,
            matrix=matrix,
            strategy=strategy,
        )

        total_game_seconds += time.perf_counter() - game_started
        guesses_used = result["guesses"]
        all_counts.append(guesses_used)

        if result["solved"]:
            solved_counts.append(guesses_used)
            distribution[str(guesses_used)] += 1
        else:
            failures += 1
            distribution["unsolved"] += 1

        if index % 25 == 0 or index == len(answers):
            print(
                "{}: evaluated {}/{} answers".format(
                    strategy, index, len(answers)
                ),
                flush=True,
            )

    elapsed = time.perf_counter() - started
    total_games = len(answers)
    solved = len(solved_counts)

    return {
        "strategy": strategy,
        "total_games": total_games,
        "solved": solved,
        "failures": failures,
        "solve_rate": solved / total_games if total_games else 0.0,
        "average_guesses_solved": (
            sum(solved_counts) / solved if solved else None
        ),
        "average_guesses_all_games": (
            sum(all_counts) / total_games if total_games else None
        ),
        "median_guesses": (
            sorted(all_counts)[len(all_counts) // 2]
            if all_counts else None
        ),
        "worst_case_guesses": max(all_counts) if all_counts else None,
        "average_runtime_seconds": (
            total_game_seconds / total_games if total_games else 0.0
        ),
        "guess_count_distribution": dict(sorted(distribution.items())),
        "benchmark_runtime_seconds": elapsed,
    }


def save_result(result, output_path):
    """Save benchmark results as JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    print("Saved results to:", output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Compare Wordle entropy and minimax strategies."
    )
    parser.add_argument(
        "--answers",
        default="data/answers_100.txt",
        help="File containing possible secret answers.",
    )
    parser.add_argument(
        "--guesses",
        default="data/allowed_guesses.txt",
        help="File containing legal guesses.",
    )
    parser.add_argument(
        "--strategy",
        choices=["entropy", "minimax", "both"],
        default="both",
        help="Strategy to benchmark.",
    )
    parser.add_argument(
        "--output",
        default="results/benchmark.json",
        help="Output JSON path. With both strategies, suffixes are added.",
    )
    args = parser.parse_args()

    answers = load_word_list(args.answers)
    legal_guesses = load_word_list(args.guesses)

    if not answers:
        raise ValueError("Answer list is empty.")
    if not legal_guesses:
        raise ValueError("Legal guess list is empty.")

    missing = sorted(set(answers) - set(legal_guesses))
    if missing:
        raise ValueError(
            "Some answers are not legal guesses, e.g. {}".format(missing[:5])
        )

    print("Answers:", len(answers))
    print("Legal guesses:", len(legal_guesses))

    matrix_started = time.perf_counter()
    matrix = FeedbackMatrix(answers, legal_guesses)
    matrix.build()
    matrix_build_seconds = time.perf_counter() - matrix_started

    print("Matrix build/load time: {:.2f}s".format(matrix_build_seconds))

    strategies = (
        ["entropy", "minimax"]
        if args.strategy == "both"
        else [args.strategy]
    )

    output_path = Path(args.output)

    for strategy in strategies:
        print("\nBenchmarking {}...".format(strategy), flush=True)

        result = benchmark_strategy(
            strategy, answers, legal_guesses, matrix
        )
        result["matrix_build_seconds"] = matrix_build_seconds
        result["answers_file"] = args.answers
        result["guesses_file"] = args.guesses

        if args.strategy == "both":
            destination = output_path.with_name(
                output_path.stem + "_" + strategy + output_path.suffix
            )
        else:
            destination = output_path

        save_result(result, destination)

        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
