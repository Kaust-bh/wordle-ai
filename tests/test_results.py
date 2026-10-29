import json

from wordle_ai.results import load_results


def test_load_results_discovers_valid_records(tmp_path):
    result = {
        "strategy": "entropy",
        "total_games": 2,
        "guess_count_distribution": {"2": 2},
    }
    (tmp_path / "valid.json").write_text(json.dumps(result), encoding="utf-8")

    records, errors = load_results(tmp_path)

    assert [record["_file"] for record in records] == ["valid.json"]
    assert errors == []


def test_load_results_skips_missing_directory(tmp_path):
    records, errors = load_results(tmp_path / "missing")

    assert records == []
    assert errors == []


def test_load_results_reports_malformed_and_incompatible_files(tmp_path):
    (tmp_path / "broken.json").write_text("{", encoding="utf-8")
    (tmp_path / "other.json").write_text(
        json.dumps({"not": "a benchmark"}),
        encoding="utf-8",
    )

    records, errors = load_results(tmp_path)

    assert records == []
    assert {filename for filename, _ in errors} == {
        "broken.json",
        "other.json",
    }