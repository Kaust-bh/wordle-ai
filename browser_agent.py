
import argparse
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from wordle_ai.feedback_matrix import FeedbackMatrix
from wordle_ai.strategies.entropy import rank_guesses
from wordle_ai.strategies.minimax import rank_minimax


WORDLE_URL = "https://www.nytimes.com/games/wordle/index.html"
DEBUG_URL = "http://127.0.0.1:9222"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

ANSWERS_FILE = DATA_DIR / "answers.txt"
GUESSES_FILE = DATA_DIR / "allowed_guesses.txt"

MAX_ATTEMPTS = 6
BOARD_SELECTOR = '[data-testid="tile"]'
POLL_INTERVAL = 0.25

STATE_TO_CODE = {
    "absent": "B",
    "present": "Y",
    "correct": "G",
}

CODE_TO_VALUE = {
    "B": 0,
    "Y": 1,
    "G": 2,
}


def load_words(path):
    if not path.exists():
        raise FileNotFoundError(f"Word list not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        words = [
            line.strip().lower()
            for line in file
            if len(line.strip()) == 5
            and line.strip().isalpha()
        ]

    return list(dict.fromkeys(words))


def encode_pattern(pattern):
    """Encode B/Y/G feedback as a base-3 integer."""

    code = 0

    for character in pattern:
        if character not in CODE_TO_VALUE:
            raise ValueError(f"Invalid feedback character: {character}")

        code = code * 3 + CODE_TO_VALUE[character]

    return code


def filter_candidates(candidates, guess, pattern, matrix):
    """Keep answers consistent with the observed feedback."""

    observed_code = encode_pattern(pattern)

    return [
        answer
        for answer in candidates
        if matrix.pattern(guess, answer) == observed_code
    ]


def choose_guess(strategy, legal_guesses, candidates, matrix):
    """Return the highest-ranked guess from the selected strategy."""

    if not candidates:
        raise RuntimeError(
            "No possible answers remain. Check the feedback and word lists."
        )

    if len(candidates) == 1:
        return candidates[0]

    if strategy == "minimax":
        results = rank_minimax(
            legal_guesses,
            candidates,
            top_k=5,
            matrix=matrix,
        )
    else:
        results = rank_guesses(
            legal_guesses,
            candidates,
            top_k=5,
            matrix=matrix,
        )

    if not results:
        raise RuntimeError("The strategy returned no guesses.")

    print("\nTop-ranked guesses:")
    for result in results[:5]:
        print(f"  {result}")

    # Both ranking functions return lists of result objects.
    guess = results[0].guess

    if guess not in legal_guesses:
        raise RuntimeError(f"Strategy returned an illegal guess: {guess}")

    return guess


def get_wordle_page(context):
    """Reuse an existing Wordle tab or open one in the same Brave context."""

    for page in context.pages:
        if "nytimes.com/games/wordle" in page.url:
            return page

    page = context.new_page()
    page.goto(WORDLE_URL, wait_until="domcontentloaded")
    return page


def wait_for_board(page, timeout=120):
    """Wait for the game's 30 tiles to appear."""

    print("Waiting for the Wordle board...")
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            if page.locator(BOARD_SELECTOR).count() >= 30:
                print("Wordle board detected.")
                return
        except Exception:
            pass

        time.sleep(POLL_INTERVAL)

    raise TimeoutError(
        "Wordle board did not appear. Check Brave for ads, consent dialogs, "
        "or other prompts and handle them normally."
    )


def read_row_states(page, row_index):
    """Read the five tile states from a submitted row."""

    tiles = page.locator(BOARD_SELECTOR)
    states = []

    for column in range(5):
        tile = tiles.nth(row_index * 5 + column)
        states.append(tile.get_attribute("data-state"))

    return states


def wait_for_feedback(page, row_index, timeout=15):
    """Wait for all five tiles to reveal their feedback."""

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            states = read_row_states(page, row_index)

            if (
                len(states) == 5
                and all(state in STATE_TO_CODE for state in states)
            ):
                return "".join(STATE_TO_CODE[state] for state in states)

        except Exception:
            pass

        time.sleep(POLL_INTERVAL)

    raise TimeoutError(
        "Could not read the submitted guess feedback. Check the board "
        "and make sure the guess was accepted."
    )


def submit_guess(page, guess):
    """Type a five-letter word and press Enter."""

    page.keyboard.type(guess, delay=70)
    page.keyboard.press("Enter")


def require_fresh_game(page):
    """Avoid confusing an existing game's rows with this solver's guesses."""

    tiles = page.locator(BOARD_SELECTOR)

    for row in range(MAX_ATTEMPTS):
        states = [
            tiles.nth(row * 5 + col).get_attribute("data-state")
            for col in range(5)
        ]

        if any(state != "empty" for state in states):
            raise RuntimeError(
                "The Wordle board already contains a guess. Start a fresh "
                "game before running this agent so its guess history stays "
                "synchronized with the board."
            )


def print_candidates(candidates, limit=20):
    print(f"\nCandidates remaining: {len(candidates)}")

    if len(candidates) <= limit:
        print(", ".join(candidates))
    else:
        print(", ".join(candidates[:limit]) + ", ...")


def run_solver(strategy, auto):
    answers = load_words(ANSWERS_FILE)
    legal_guesses = load_words(GUESSES_FILE)

    print(f"Loaded {len(answers)} possible answers.")
    print(f"Loaded {len(legal_guesses)} legal guesses.")
    print(f"Strategy: {strategy}")

    matrix = FeedbackMatrix(answers, legal_guesses)
    matrix.build(cache_dir=str(DATA_DIR / "cache"))

    candidates = answers.copy()
    history = []

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(DEBUG_URL)

        try:
            if not browser.contexts:
                raise RuntimeError("No Brave browser context was found.")

            context = browser.contexts[0]
            page = get_wordle_page(context)

            wait_for_board(page)
            require_fresh_game(page)

            print("\nConnected to Brave.")
            print("Use a fresh Wordle game for this run.")
            print("Press Ctrl+C to stop.")

            for turn in range(MAX_ATTEMPTS):
                print(f"\n{'=' * 36}")
                print(f"GUESS {turn + 1}/{MAX_ATTEMPTS}")
                print(f"{'=' * 36}")

                guess = choose_guess(
                    strategy,
                    legal_guesses,
                    candidates,
                    matrix,
                )

                print(f"\nSuggested guess: {guess.upper()}")

                if auto:
                    confirmation = input(
                        "Press Enter to submit, or type q to quit: "
                    ).strip().lower()

                    if confirmation == "q":
                        print("Stopped before submitting.")
                        break
                else:
                    confirmation = input(
                        "Press Enter to submit this guess, "
                        "or type q to quit: "
                    ).strip().lower()

                    if confirmation == "q":
                        print("Stopped before submitting.")
                        break

                submit_guess(page, guess)

                pattern = wait_for_feedback(page, turn)
                history.append((guess, pattern))

                print(f"Guess:    {guess.upper()}")
                print(f"Feedback: {pattern}")

                if pattern == "GGGGG":
                    print(f"\nSolved in {turn + 1} guess(es)!")
                    break

                candidates = filter_candidates(
                    candidates,
                    guess,
                    pattern,
                    matrix,
                )

                print_candidates(candidates)

                if not candidates:
                    print(
                        "\nNo candidates remain. Check whether the observed "
                        "tile colors and answer list match the puzzle."
                    )
                    break

            print("\nGuess history:")
            for number, (word, pattern) in enumerate(history, start=1):
                print(f"{number}. {word.upper()} -> {pattern}")

        finally:
            # Disconnect Playwright. Do not explicitly close Brave's
            # context or tabs.
            browser.close()


def main():
    parser = argparse.ArgumentParser(
        description="Wordle AI agent connected to an existing Brave session."
    )

    parser.add_argument(
        "--strategy",
        choices=["minimax", "entropy"],
        default="minimax",
        help="Guess-selection strategy (default: minimax).",
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Enable submission without a confirmation prompt.",
    )

    args = parser.parse_args()

    try:
        run_solver(args.strategy, args.auto)
    except KeyboardInterrupt:
        print("\nSolver stopped.")
    except Exception as error:
        print(f"\nError: {error}")
        raise


if __name__ == "__main__":
    main()
