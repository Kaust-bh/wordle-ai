import streamlit as st
import pandas as pd

st.set_page_config(page_title="Wordle AI Benchmarks", page_icon="🟩", layout="wide")
st.title("Wordle AI Benchmark Dashboard")
st.caption("Reported 2,315-answer benchmark snapshot. Re-run before publishing.")

summary = pd.DataFrame([
    {"Strategy": "Entropy", "Answers": 2315, "Solved": 2315, "Average guesses": 3.52786,
     "Median guesses": 4, "Worst case": 6, "Seconds/game": 0.27075, "Total seconds": 626.8},
    {"Strategy": "Minimax", "Answers": 2315, "Solved": 2315, "Average guesses": 3.52268,
     "Median guesses": 4, "Worst case": 5, "Seconds/game": 0.21534, "Total seconds": 498.5},
])
distribution = pd.DataFrame({
    "Guesses": [1, 2, 3, 4, 5, 6],
    "Entropy": [0, 31, 1100, 1116, 67, 1],
    "Minimax": [1, 67, 1040, 1135, 72, 0],
}).set_index("Guesses")

st.warning("Snapshot values, not a live run. Results depend on the exact word lists, implementation, tie-breaks, and machine.")
a, b, c, d = st.columns(4)
a.metric("Answers evaluated", "2,315")
b.metric("Entropy average", "3.528")
c.metric("Minimax average", "3.523")
d.metric("Minimax worst case", "5")

st.subheader("Strategy comparison")
st.dataframe(summary.style.format({
    "Average guesses": "{:.4f}", "Seconds/game": "{:.4f}", "Total seconds": "{:.1f}"
}), use_container_width=True, hide_index=True)

st.subheader("Guess-count distribution")
st.bar_chart(distribution, use_container_width=True)

st.subheader("Interpretation")
st.markdown(
    "- Minimax had a slightly lower average guess count in this run.\n"
    "- Minimax's worst case was five guesses versus six for entropy.\n"
    "- Both reportedly solved all 2,315 tested answers.\n"
    "- Compare only runs using the same lists and evaluation protocol."
)
st.info("Next step: update this dashboard to load JSON emitted by your benchmark runner, so results refresh reproducibly.")
