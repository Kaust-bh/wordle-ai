
"""Wordle AI Arena: interactive entropy and minimax solver."""

import random
import time

import streamlit as st

from wordle_ai.feedback import score_guess
from wordle_ai.feedback_matrix import FeedbackMatrix
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


def new_game():
    st.session_state.secret = random.choice(answers)
    st.session_state.candidates = list(answers)
    st.session_state.history = []
    st.session_state.status = "playing"


if "secret" not in st.session_state:
    new_game()

if "strategy" not in st.session_state:
    st.session_state.strategy = "Minimax"


def take_turn():
    """Play one turn using the currently selected strategy."""
    if st.session_state.status != "playing":
        return

    candidates = st.session_state.candidates
    strategy = st.session_state.strategy
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

    st.session_state.candidates = [
        word for word in candidates
        if score_guess(guess, word) == pattern
    ]

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


st.title("🟩 Wordle AI Arena")
st.caption("Compare information theory with minimax decision-making.")

st.selectbox(
    "AI strategy",
    ["Minimax", "Entropy"],
    key="strategy",
    help=(
        "Minimax minimizes the largest possible remaining candidate "
        "group. Entropy maximizes expected information gain."
    ),
)

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
        strategy = st.session_state.strategy
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
