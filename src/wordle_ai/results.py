"""Loading and validating saved benchmark results."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results"


def load_results(results_dir=DEFAULT_RESULTS_DIR):
    """Return benchmark records and file-level load errors."""
    records = []
    errors = []
    results_dir = Path(results_dir)

    if not results_dir.is_dir():
        return records, errors

    for path in sorted(results_dir.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append((path.name, str(exc)))
            continue

        if not isinstance(data, dict) or not _is_benchmark_result(data):
            errors.append((path.name, "not a benchmark result object"))
            continue

        data["_file"] = path.name
        records.append(data)

    return records, errors


def _is_benchmark_result(data):
    """Identify the schema emitted by wordle_ai.benchmark."""
    return (
        isinstance(data.get("strategy"), str)
        and "total_games" in data
        and isinstance(data.get("guess_count_distribution"), dict)
    )