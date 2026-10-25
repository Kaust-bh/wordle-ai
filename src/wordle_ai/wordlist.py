"""Load and validate newline-separated word lists."""

from pathlib import Path
from typing import List


def load_word_list(path: str, word_length: int = 5) -> List[str]:
    """Load unique lowercase words, ignoring blank lines and comments."""
    file_path = Path(path)

    if not file_path.is_file():
        raise FileNotFoundError("Word list not found: {}".format(path))

    words = []
    seen = set()

    for line_number, line in enumerate(
        file_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        word = line.strip().lower()

        if not word or word.startswith("#"):
            continue

        if len(word) != word_length or not word.isalpha() or not word.isascii():
            raise ValueError(
                "Invalid word at line {} in {}: {!r}".format(
                    line_number, path, line.strip()
                )
            )

        if word not in seen:
            words.append(word)
            seen.add(word)

    if not words:
        raise ValueError("Word list is empty: {}".format(path))

    return words
