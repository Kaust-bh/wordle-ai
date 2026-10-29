
"""Wordle AI Arena: interactive entropy and minimax solver."""

import random
import time

import streamlit as st
from st_keyup import st_keyup

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from wordle_ai.feedback import score_guess
from wordle_ai.feedback_matrix import FeedbackMatrix
from wordle_ai.arena import (
    apply_keyboard_input,
    compare_results,
    filter_candidates,
    normalize_custom_word,
    sanitize_keyboard_text,
    solve_target as run_solver,
    update_keyboard_state,
)
from wordle_ai.game import GameState
from wordle_ai.strategies.entropy import rank_guesses
from wordle_ai.strategies.minimax import rank_minimax
from wordle_ai.wordlist import load_word_list


st.set_page_config(
    page_title="Wordle AI Arena",
    page_icon="🟩",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
    }
    .board {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        margin: 24px 0;
    }
    .board-row { display: flex; gap: 6px; }
    .tile {
        width: 54px;
        height: 54px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px solid #d3d6da;
        border-radius: 4px;
        font-size: 24px;
        font-weight: 800;
        color: white;
        text-transform: uppercase;
    }
    .correct { background: #6aaa64; border-color: #6aaa64; }
    .present { background: #c9b458; border-color: #c9b458; }
    .absent { background: #787c7e; border-color: #787c7e; }
    .empty { background: transparent; color: #222; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Loading word lists and feedback matrix...")
def load_engine():
    answers = load_word_list("data/answers_1k.txt")
    guesses = load_word_list("data/allowed_guesses.txt")

    missing = set(answers) - set(guesses)
    if missing:
        raise ValueError(
            "Some answers are missing from allowed_guesses.txt"
        )

    matrix = FeedbackMatrix(answers, guesses)
    matrix.build()
    return answers, guesses, matrix


answers, legal_guesses, matrix = load_engine()


def get_rankings(strategy, candidates, top_k=5):
    """Use the selected strategy with the shared feedback matrix."""
    if strategy == "Entropy":
        return rank_guesses(
            legal_guesses,
            candidates,
            top_k=top_k,
            matrix=matrix,
        )

    return rank_minimax(
        legal_guesses,
        candidates,
        top_k=top_k,
        matrix=matrix,
    )


MODES = ["AI Solver", "Custom Word Challenge", "Human vs AI"]
STRATEGIES = ["Minimax", "Entropy"]


def reset_ai_game(secret=None, strategy=None):
    """Reset the shared AI solver state for a new target."""
    st.session_state.secret = secret or random.choice(answers)
    st.session_state.candidates = list(answers)
    st.session_state.history = []
    st.session_state.status = "playing"
    st.session_state.game_strategy = (
        strategy
        if strategy is not None
        else st.session_state.strategy_selector
    )


def new_game():
    """Keep the original AI Solver reset entry point."""
    reset_ai_game()


def reset_human_game(secret, strategy):
    """Create a human game and precompute the AI race on the same target."""
    st.session_state.secret = secret
    st.session_state.human_game = GameState(secret, legal_guesses)
    st.session_state.human_history = []
    st.session_state.keyboard = {}
    st.session_state.human_guess_buffer = ""
    st.session_state.human_input_version = 0
    st.session_state.human_submit_requested = False
    st.session_state.ai_history = solve_target(secret, strategy)
    st.session_state.human_status = "playing"
    st.session_state.ai_solved = (
        bool(st.session_state.ai_history)
        and st.session_state.ai_history[-1]["guess"] == secret
    )


def solve_target(secret, strategy):
    """Run the existing strategy against one target."""
    return run_solver(secret, answers, legal_guesses, matrix, strategy)


def initialize_state():
    if "game_mode" not in st.session_state:
        st.session_state.game_mode = "AI Solver"
    if "strategy_selector" not in st.session_state:
        st.session_state.strategy_selector = "Minimax"
    if "game_strategy" not in st.session_state:
        st.session_state.game_strategy = st.session_state.strategy_selector
    if "secret" not in st.session_state:
        reset_ai_game()


initialize_state()


def take_turn():
    """Play one turn using the currently selected strategy."""
    if st.session_state.status != "playing":
        return

    candidates = st.session_state.candidates
    strategy = st.session_state.game_strategy
    rankings = get_rankings(strategy, candidates, top_k=5)

    if not rankings:
        st.session_state.status = "failed"
        return

    result = rankings[0]
    guess = result.guess
    pattern = score_guess(guess, st.session_state.secret)

    entry = {
        "guess": guess,
        "pattern": pattern,
        "strategy": strategy,
        "candidate_count": len(candidates),
        "entropy": getattr(result, "entropy", None),
        "expected_remaining": result.expected_remaining,
        "worst_case_remaining": result.worst_case_remaining,
        "solve_probability": result.solve_probability,
    }
    st.session_state.history.append(entry)

    if guess == st.session_state.secret:
        st.session_state.status = "won"
        return

    st.session_state.candidates = filter_candidates(
        candidates, guess, pattern
    )

    if len(st.session_state.history) >= 6:
        st.session_state.status = "failed"


def render_board():
    html = '<div class="board">'

    for row_index in range(6):
        html += '<div class="board-row">'

        if row_index < len(st.session_state.history):
            entry = st.session_state.history[row_index]

            for letter, mark in zip(
                entry["guess"], entry["pattern"]
            ):
                css_class = {
                    "G": "correct",
                    "Y": "present",
                    "B": "absent",
                }[mark]

                html += (
                    f'<div class="tile {css_class}">'
                    f'{letter}</div>'
                )
        else:
            for _ in range(5):
                html += '<div class="tile empty"></div>'

        html += "</div>"

    return html + "</div>"


def render_status():
    if st.session_state.status == "won":
        return (
            f"Solved in {len(st.session_state.history)} guesses! "
            f"Answer: {st.session_state.secret.upper()}"
        )

    if st.session_state.status == "failed":
        return f"Game over. Answer: {st.session_state.secret.upper()}"

    return (
        f"Possible answers remaining: "
        f"{len(st.session_state.candidates)}"
    )


def render_history_board(history, current_guess=""):
    """Render a six-row board for submitted history and current input."""
    html = '<div class="board">'
    for row_index in range(6):
        html += '<div class="board-row">'
        if row_index < len(history):
            entry = history[row_index]
            for letter, mark in zip(entry["guess"], entry["pattern"]):
                css_class = {
                    "G": "correct",
                    "Y": "present",
                    "B": "absent",
                }[mark]
                html += (
                    f'<div class="tile {css_class}">{letter}</div>'
                )
        elif row_index == len(history) and current_guess:
            html += "".join(
                f'<div class="tile empty">{letter}</div>'
                for letter in current_guess
            )
            html += '<div class="tile empty"></div>' * (
                5 - len(current_guess)
            )
        else:
            html += '<div class="tile empty"></div>' * 5
        html += "</div>"
    return html + "</div>"


def render_keyboard(keyboard):
    """Render a clickable, colored QWERTY keyboard."""
    rows = (
        ("q", "w", "e", "r", "t", "y", "u", "i", "o", "p"),
        ("a", "s", "d", "f", "g", "h", "j", "k", "l"),
        ("enter", "z", "x", "c", "v", "b", "n", "m", "backspace"),
    )
    colors = {
        "G": ("#6aaa64", "#ffffff"),
        "Y": ("#c9b458", "#ffffff"),
        "B": ("#787c7e", "#ffffff"),
        "default": ("#f8f9fa", "#202124"),
    }
    disabled = st.session_state.human_status != "playing"
    clicked_key = None

    for row in rows:
        columns = st.columns(len(row))
        for column, letter in zip(columns, row):
            with column:
                mark = keyboard.get(letter) if len(letter) == 1 else None
                background, foreground = colors.get(
                    mark, colors["default"]
                )
                container_key = f"keyboard-key-{letter}"
                st.markdown(
                    f"""
                    <style>
                    .st-key-{container_key} button {{
                        background: {background} !important;
                        border-color: {background} !important;
                        color: {foreground} !important;
                        font-weight: 700 !important;
                        min-height: 42px;
                    }}
                    .st-key-{container_key} button:hover {{
                        filter: brightness(0.92);
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                with st.container(key=container_key):
                    label = {
                        "enter": "ENTER",
                        "backspace": "BACKSPACE",
                    }.get(letter, letter.upper())
                    if st.button(
                        label,
                        key=f"keyboard-button-{letter}",
                        disabled=disabled,
                        use_container_width=True,
                    ):
                        clicked_key = letter

    return clicked_key


def request_human_submit():
    """Record physical Enter without modifying the input widget state."""
    st.session_state.human_submit_requested = True


def sync_human_input(input_key):
    """Copy a keyup event into the canonical guess buffer."""
    raw_value = st.session_state.get(input_key, "")
    guess_value = sanitize_keyboard_text(raw_value)
    st.session_state.human_guess_buffer = guess_value
    if guess_value != raw_value:
        st.session_state.human_input_version += 1


def submit_human_input(input_key):
    """Synchronize the latest physical input and request one submission."""
    sync_human_input(input_key)
    request_human_submit()


st.title("🟩 Wordle AI Arena")
st.caption("Compare information theory with minimax decision-making.")

previous_mode = st.session_state.get("last_game_mode", "AI Solver")
selected_mode = st.selectbox(
    "Game mode",
    MODES,
    index=MODES.index(st.session_state.game_mode),
    key="game_mode",
)

if selected_mode != previous_mode:
    st.session_state.last_game_mode = selected_mode
    st.session_state.human_guess_buffer = ""
    if selected_mode == "AI Solver":
        reset_ai_game()
    elif selected_mode == "Custom Word Challenge":
        st.session_state.status = "setup"
        st.session_state.custom_status = "setup"
    else:
        st.session_state.human_status = "setup"
    st.rerun()

st.session_state.last_game_mode = selected_mode

if selected_mode == "Custom Word Challenge":
    st.subheader("Custom Word Challenge")
    st.write("Choose a supported answer word and let the AI solve it.")
    st.selectbox(
        "AI strategy",
        STRATEGIES,
        key="strategy_selector",
        disabled=st.session_state.get("status") == "playing",
    )

    if st.session_state.get("status") != "playing":
        custom_word = st.text_input(
            "Secret five-letter word",
            key="custom_word",
            max_chars=5,
            type="password",
            help="The word is hidden while the AI is solving.",
        )
        if st.button("Start Challenge", type="primary"):
            word, error = normalize_custom_word(custom_word, answers)
            if error:
                st.error(error)
            else:
                reset_ai_game(word, st.session_state.strategy_selector)
                st.rerun()
    else:
        st.info("Your word is hidden while the AI solves it.")

    if st.session_state.get("status") in ("playing", "won", "failed"):
        st.markdown(render_board(), unsafe_allow_html=True)
        if st.session_state.status == "won":
            st.success(render_status())
        elif st.session_state.status == "failed":
            st.error(render_status())
        else:
            st.info(
                f"Guesses used: {len(st.session_state.history)} / 6"
            )

        next_col, new_col = st.columns(2)
        with next_col:
            if st.button(
                "▶ Next Guess",
                disabled=st.session_state.status != "playing",
                use_container_width=True,
            ):
                take_turn()
                st.rerun()
        with new_col:
            if st.button("Play Again", use_container_width=True):
                st.session_state.status = "setup"
                st.session_state.history = []
                st.rerun()

        if st.session_state.history:
            st.subheader("AI guess sequence")
            st.dataframe(
                [
                    {
                        "Guess": entry["guess"].upper(),
                        "Feedback": entry["pattern"],
                    }
                    for entry in st.session_state.history
                ],
                hide_index=True,
                use_container_width=True,
            )

    st.stop()

if selected_mode == "Human vs AI":
    st.subheader("Human vs AI")
    st.caption("You and the AI are solving the same hidden word.")
    st.selectbox(
        "AI strategy",
        STRATEGIES,
        key="strategy_selector",
        disabled=st.session_state.get("human_status") == "playing",
    )

    if st.session_state.get("human_status") in (None, "setup"):
        if st.button("Start Human vs AI", type="primary"):
            reset_human_game(
                random.choice(answers), st.session_state.strategy_selector
            )
            st.session_state.human_guess_buffer = ""
            st.rerun()
        st.info("The AI will choose a word from the supported answer list.")
        st.stop()

    if st.session_state.human_status == "playing":
        input_key = (
            f"human_guess_input_"
            f"{st.session_state.get('human_input_version', 0)}"
        )
        st_keyup(
            "Your guess",
            value=st.session_state.get("human_guess_buffer", ""),
            max_chars=5,
            key=input_key,
            debounce=0,
            on_change=sync_human_input,
            args=(input_key,),
            on_submit=submit_human_input,
            submit_args=(input_key,),
            placeholder="Type A-Z, then press Enter",
        )
        guess_value = st.session_state.human_guess_buffer
        st.markdown(
            render_history_board(
                st.session_state.human_history, guess_value
            ),
            unsafe_allow_html=True,
        )
        clicked_key = render_keyboard(st.session_state.keyboard)

        submit_guess = st.session_state.pop(
            "human_submit_requested", False
        )
        if clicked_key:
            if clicked_key == "enter":
                submit_guess = True
            else:
                st.session_state.human_guess_buffer = apply_keyboard_input(
                    guess_value, clicked_key
                )
                st.session_state.human_input_version = (
                    st.session_state.get("human_input_version", 0) + 1
                )
                st.rerun()

        if submit_guess:
            try:
                pattern, game_over = st.session_state.human_game.submit_guess(
                    guess_value
                )
            except ValueError as error:
                st.error(str(error))
            else:
                st.session_state.human_history.append({
                    "guess": guess_value.strip().lower(),
                    "pattern": pattern,
                })
                st.session_state.keyboard = update_keyboard_state(
                    st.session_state.keyboard,
                    guess_value.strip().lower(),
                    pattern,
                )
                st.session_state.human_guess_buffer = ""
                st.session_state.human_input_version = (
                    st.session_state.get("human_input_version", 0) + 1
                )
                if pattern == "GGGGG":
                    st.session_state.human_status = "won"
                elif game_over:
                    st.session_state.human_status = "failed"
                st.rerun()
    else:
        comparison = compare_results(
            st.session_state.human_history,
            st.session_state.human_status == "won",
            st.session_state.ai_history,
            st.session_state.ai_solved,
        )
        if st.session_state.human_status == "won":
            st.success(
                f"You solved it in {comparison['human_guesses']} guesses."
            )
        else:
            st.error("You did not solve the word in six guesses.")

        st.info(f"The hidden word was {st.session_state.secret.upper()}.")
        st.subheader("Race result")
        if comparison["winner"] == "tie":
            st.success("Tie: you and the AI used the same number of guesses.")
        elif comparison["winner"] == "human":
            st.success("You solved the word in fewer guesses.")
        elif comparison["winner"] == "ai":
            st.info("The AI solved the word in fewer guesses.")
        else:
            st.warning("Neither solver found the word within six guesses.")

        st.write({
            "Human guesses": comparison["human_guesses"] or "Failed",
            "AI guesses": comparison["ai_guesses"] or "Failed",
        })
        st.subheader("Complete guess sequences")
        st.write({
            "Human": [entry["guess"].upper() for entry in st.session_state.human_history],
            "AI": [entry["guess"].upper() for entry in st.session_state.ai_history],
        })
        if st.button("Play Again", type="primary"):
            st.session_state.human_status = "setup"
            st.session_state.human_history = []
            st.session_state.ai_history = []
            st.session_state.keyboard = {}
            st.rerun()

    st.stop()

st.selectbox(
    "AI strategy",
    ["Minimax", "Entropy"],
    key="strategy_selector",
    help=(
        "Minimax minimizes the largest possible remaining candidate "
        "group. Entropy maximizes expected information gain."
    ),
)

if (
    st.session_state.get("last_strategy") is not None
    and st.session_state.last_strategy != st.session_state.strategy_selector
    and st.session_state.status == "playing"
):
    reset_ai_game(strategy=st.session_state.strategy_selector)
    st.session_state.last_strategy = st.session_state.strategy_selector
    st.rerun()

st.session_state.last_strategy = st.session_state.strategy_selector

board_column, analysis_column = st.columns([1, 1.25], gap="large")

with board_column:
    st.subheader("Live game")

    board_slot = st.empty()
    status_slot = st.empty()

    board_slot.markdown(render_board(), unsafe_allow_html=True)

    if st.session_state.status == "won":
        status_slot.success(render_status())
    elif st.session_state.status == "failed":
        status_slot.error(render_status())
    else:
        status_slot.info(render_status())

    next_col, new_col = st.columns(2)

    with next_col:
        next_clicked = st.button(
            "▶ Next Guess",
            use_container_width=True,
            disabled=st.session_state.status != "playing",
        )

    with new_col:
        new_clicked = st.button(
            "🔄 New Game",
            use_container_width=True,
        )

    autoplay_clicked = st.button(
        "⏩ Autoplay Game",
        use_container_width=True,
        disabled=st.session_state.status != "playing",
    )

    if new_clicked:
        new_game()
        st.rerun()

    if next_clicked:
        take_turn()
        st.rerun()

    if autoplay_clicked:
        while st.session_state.status == "playing":
            take_turn()

            board_slot.markdown(
                render_board(), unsafe_allow_html=True
            )

            if st.session_state.status == "won":
                status_slot.success(render_status())
            elif st.session_state.status == "failed":
                status_slot.error(render_status())
            else:
                status_slot.info(render_status())

            time.sleep(0.65)

        st.rerun()


with analysis_column:
    st.subheader("🧠 AI Thinking Panel")

    st.metric("Possible answers", len(st.session_state.candidates))
    st.metric("Guesses used", len(st.session_state.history))

    if st.session_state.status == "playing":
        strategy = st.session_state.game_strategy
        rankings = get_rankings(
            strategy,
            st.session_state.candidates,
            top_k=5,
        )

        if rankings:
            best = rankings[0]

            st.markdown("#### Recommended next guess")
            st.markdown(f"# `{best.guess.upper()}`")

            if strategy == "Minimax":
                st.caption(
                    "Selected by minimizing the worst-case "
                    "remaining candidate group."
                )
                st.metric(
                    "Worst-case remaining",
                    best.worst_case_remaining,
                )
                col1, col2 = st.columns(2)
                col1.metric(
                    "Expected remaining",
                    f"{best.expected_remaining:.2f}",
                )
                col2.metric(
                    "Immediate solve chance",
                    f"{best.solve_probability * 100:.2f}%",
                )
            else:
                st.caption(
                    "Selected by maximizing information entropy."
                )
                col1, col2 = st.columns(2)
                col1.metric("Entropy", f"{best.entropy:.3f} bits")
                col2.metric(
                    "Expected remaining",
                    f"{best.expected_remaining:.2f}",
                )
                st.metric(
                    "Worst-case remaining",
                    best.worst_case_remaining,
                )

            st.markdown("#### Top 5 guesses")

            table = []
            for i, item in enumerate(rankings, start=1):
                row = {
                    "Rank": i,
                    "Guess": item.guess.upper(),
                    "Worst case": item.worst_case_remaining,
                    "Expected left": round(
                        item.expected_remaining, 2
                    ),
                    "Solve chance (%)": round(
                        item.solve_probability * 100, 2
                    ),
                }

                entropy_value = getattr(item, "entropy", None)
                if entropy_value is not None:
                    row["Entropy (bits)"] = round(entropy_value, 3)

                table.append(row)

            st.dataframe(
                table,
                hide_index=True,
                use_container_width=True,
            )

    elif st.session_state.status == "won":
        st.success("The solver found the answer.")
    else:
        st.info("Game over. Start a new game to continue.")


st.divider()
st.subheader("📜 Guess history")

if not st.session_state.history:
    st.caption("No guesses yet.")
else:
    for turn, entry in enumerate(st.session_state.history, start=1):
        with st.expander(
            f"Turn {turn}: {entry['guess'].upper()} "
            f"({entry['strategy']})",
            expanded=(turn == len(st.session_state.history)),
        ):
            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Candidates before",
                entry["candidate_count"],
            )

            if entry["entropy"] is not None:
                col2.metric(
                    "Entropy",
                    f"{entry['entropy']:.3f} bits",
                )
            else:
                col2.metric(
                    "Worst-case remaining",
                    entry["worst_case_remaining"],
                )

            col3.metric(
                "Expected remaining",
                f"{entry['expected_remaining']:.2f}",
            )


with st.expander("How the strategies work"):
    st.markdown(
        """
        **Minimax**
        1. Simulate feedback for each legal guess against the remaining
           possible answers.
        2. Find the largest group of answers that any feedback pattern
           could leave behind.
        3. Choose the guess with the smallest largest group.

        **Entropy**
        1. Calculate the probabilities of possible feedback patterns.
        2. Measure the uncertainty of that distribution in bits.
        3. Choose the guess with the highest entropy.

        Both strategies use the same precomputed feedback matrix.
        Neither is a trained neural network.

        The demo uses `answers_1k.txt`, a 1,000-answer subset.
        """
    )

st.caption(
    "Wordle AI Arena · Local simulation · Entropy + Minimax"
)
