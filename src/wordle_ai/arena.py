"""Pure helpers shared by the interactive Wordle Arena modes."""

from .feedback import score_guess
from .strategies.entropy import rank_guesses
from .strategies.minimax import rank_minimax


def normalize_custom_word(value, answer_words):
    """Normalize and validate a custom target against the answer list."""
    if not isinstance(value, str):
        return None, "Enter a five-letter word."

    word = value.strip().lower()
    if len(word) != 5 or not word.isascii() or not word.isalpha():
        return None, "The secret word must contain exactly five letters."
    if word not in set(answer_words):
        return None, "That word is not in the supported answer list."

    return word, None


def update_keyboard_state(keyboard, guess, pattern):
    """Merge feedback into keyboard colors, keeping the strongest mark."""
    priority = {"B": 0, "Y": 1, "G": 2}
    updated = dict(keyboard)
    for letter, mark in zip(guess, pattern):
        current_mark = updated.get(letter)
        if priority[mark] > priority.get(current_mark, -1):
            updated[letter] = mark
    return updated


def apply_keyboard_input(current_guess, key):
    """Apply one physical or on-screen keyboard key to a guess buffer."""
    current_guess = current_guess.strip().lower()
    key = key.strip().lower()

    if key == "backspace":
        return current_guess[:-1]
    if key == "enter":
        return current_guess
    if (
        len(key) == 1
        and key.isascii()
        and key.isalpha()
        and len(current_guess) < 5
    ):
        return current_guess + key
    return current_guess


def sanitize_keyboard_text(value):
    """Keep only ASCII letters from physical or pasted keyboard input."""
    if not isinstance(value, str):
        return ""
    return "".join(
        character.lower()
        for character in value
        if character.isascii() and character.isalpha()
    )[:5]


def compare_results(human_guesses, human_solved, ai_history, ai_solved):
    """Compare human and AI outcomes without exposing either target."""
    human_count = len(human_guesses) if human_solved else None
    ai_count = len(ai_history) if ai_solved else None

    if human_solved and ai_solved:
        if human_count < ai_count:
            winner = "human"
        elif ai_count < human_count:
            winner = "ai"
        else:
            winner = "tie"
    elif human_solved:
        winner = "human"
    elif ai_solved:
        winner = "ai"
    else:
        winner = "neither"

    return {
        "human_guesses": human_count,
        "ai_guesses": ai_count,
        "winner": winner,
    }


def keyboard_from_history(history):
    """Build keyboard state from entries containing guess and pattern."""
    keyboard = {}
    for entry in history:
        keyboard = update_keyboard_state(
            keyboard, entry["guess"], entry["pattern"]
        )
    return keyboard


def filter_candidates(candidates, guess, pattern):
    """Keep answers consistent with one shared feedback result."""
    return [
        answer for answer in candidates
        if score_guess(guess, answer) == pattern
    ]


def solve_target(secret, answers, legal_guesses, matrix, strategy):
    """Solve one target using the selected existing ranking strategy."""
    candidates = list(answers)
    history = []
    ranker = rank_guesses if strategy == "Entropy" else rank_minimax

    while len(history) < 6 and candidates:
        rankings = ranker(
            legal_guesses,
            candidates,
            top_k=5,
            matrix=matrix,
        )
        if not rankings:
            break

        result = rankings[0]
        guess = result.guess
        pattern = score_guess(guess, secret)
        history.append({
            "guess": guess,
            "pattern": pattern,
            "strategy": strategy,
            "candidate_count": len(candidates),
            "entropy": getattr(result, "entropy", None),
            "expected_remaining": result.expected_remaining,
            "worst_case_remaining": result.worst_case_remaining,
            "solve_probability": result.solve_probability,
        })

        if guess == secret:
            break
        candidates = filter_candidates(candidates, guess, pattern)

    return history