# Publishing checklist

- Re-run entropy and minimax on the same word lists.
- Confirm reported benchmark values against fresh output.
- Record word-list provenance, Python/package versions, and hardware.
- Run `PYTHONPATH=src python3 -m pytest -q`.
- Test `streamlit run benchmark_dashboard.py`.
- Inspect the actual repository tree and adjust README paths/commands.
- Do not commit browser profiles, cookies, secrets, virtual environments, or cache files.
- Add a screenshot/GIF of the arena.
- Choose a license intentionally before describing the project as open source.
