# Wordle AI

An AI-powered Wordle solver that uses information theory, entropy maximization, and minimax search to identify efficient guesses and solve Wordle puzzles.

The project includes two guessing strategies, a precomputed feedback matrix for faster evaluation, benchmarking tools, and an interactive Streamlit application.

## Features

- **Entropy-based strategy:** Ranks guesses by expected information gain, helping narrow down the remaining candidate words.
- **Minimax strategy:** Selects guesses that minimize the size of the largest possible remaining candidate group.
- **Optimized feedback matrix:** Precomputes Wordle feedback patterns for word pairs, reducing repeated calculations.
- **Interactive AI Arena:** Play simulated Wordle games, view AI suggestions, and observe the solving process.
- **Benchmarking:** Compare strategies using average guesses, worst-case performance, solve rate, and execution time.
- **Automated tests:** Tests cover feedback generation, candidate filtering, game logic, and guessing strategies.

## How It Works

### 1. Wordle feedback

Every guess receives a pattern of green, yellow, and grey tiles. The solver uses this feedback to eliminate words that cannot be the answer.

Repeated letters are handled according to Wordle's feedback rules.

### 2. Entropy maximization

The entropy strategy evaluates how a guess is expected to divide the remaining candidate words across possible feedback patterns.

A guess with higher expected information gain can eliminate more uncertainty on average.

### 3. Minimax search

The minimax strategy evaluates the possible feedback patterns for each guess and selects a guess that minimizes the largest resulting candidate group.

This approach focuses on limiting the worst-case number of remaining possibilities.

### 4. Precomputed feedback matrix

The feedback matrix stores the result of comparing guesses against possible answers. Both strategies can reuse these results instead of repeatedly calculating feedback.

The matrix is cached locally to reduce setup time on subsequent runs.

## Project Structure

```text
wordle-ai/
├── app.py
├── benchmark_dashboard.py
├── data/
│   ├── answers.txt
│   ├── answers_1k.txt
│   ├── answers_100.txt
│   └── allowed_guesses.txt
├── docs/
│   └── architecture.mmd
├── src/
│   └── wordle_ai/
│       ├── candidates.py
│       ├── feedback.py
│       ├── feedback_matrix.py
│       ├── game.py
│       ├── wordlist.py
│       └── strategies/
│           ├── entropy.py
│           └── minimax.py
├── tests/
├── benchmark.py
├── pyproject.toml
└── requirements.txt
```

## Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/Kaust-bh/wordle-ai.git
cd wordle-ai
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install the project in editable mode if required by your environment:

```bash
pip install -e .
```

## Running the AI Arena

Launch the Streamlit application:

```bash
PYTHONPATH=src python3 -m streamlit run app.py
```

The Arena lets you play simulated Wordle games, request AI guesses, inspect the game history, and compare the strategies interactively.

## Running Benchmarks

Run both strategies:

```bash
PYTHONPATH=src python3 -m wordle_ai.benchmark --strategy both
```

Depending on the benchmark configuration, execution may take several minutes because the solver evaluates many possible answers.

Benchmark results are meaningful only when the strategies use the same answer list and comparable configurations. Runtime also depends on the machine, Python version, dependency versions, and caching.

### Metrics

| Metric | Description |
|---|---|
| Average guesses | Mean number of guesses required to solve the answer |
| Worst-case guesses | Maximum guesses required across evaluated answers |
| Solve rate | Percentage of evaluated answers solved within the guess limit |
| Runtime | Time taken to evaluate the strategy |

## Testing

Run the test suite:

```bash
PYTHONPATH=src python3 -m pytest -q
```

The tests cover core feedback rules, candidate filtering, game behavior, word-list handling, and strategy logic.

## Technology Stack

- **Python** — solver implementation and benchmarking
- **NumPy** — vectorized feedback-matrix operations
- **Streamlit** — interactive AI Arena
- **pytest** — automated testing

## Future Improvements

- Add more search strategies and hybrid entropy–minimax approaches.
- Visualize how candidate counts change after each guess.
- Compare strategies across different answer-list sizes.
- Improve benchmark reporting and reproducibility.
- Add configurable difficulty and evaluation settings to the Arena.

## Author

Developed by [Kaust-bh](https://github.com/Kaust-bh).

