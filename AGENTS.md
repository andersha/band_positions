# Repository Guidelines

## Project Structure & Module Organization
Core logic resides in `src/nmjanitsjar_scraper/`, with `cli.py` orchestrating modules such as `url_discovery.py`, `parser.py`, `exporter.py`, and `analytics.py`. Cache data under `data/json/` and `data/processed/`; oversized HTML lives in ignored `data/raw/`. Store metadata seeds in `meta/`, exploratory notebooks in `notebooks/`, and logs or ad hoc outputs in `logs/`. Mirror this layout inside `tests/` when adding coverage.

## Build, Test, and Development Commands
- `poetry install` — install all runtime and dev dependencies.
- `poetry run python -m src.nmjanitsjar_scraper.cli pipeline --years 2024 2025` — run the end-to-end scrape for specific seasons.
- `poetry run pytest` — execute the test suite; add `-k` for targeted runs.
- `poetry run python quick_analysis.py` — generate a fast health check of the latest processed data.

## Coding Style & Naming Conventions
Target Python 3.10 with 4-space indentation, type hints, and snake_case modules/files (`piece_analysis.py`). Keep CLI subcommands short and hyphen-free. Before committing, format with `poetry run black src tests` and `poetry run isort src tests`, then lint via `poetry run flake8 src tests`. Document Pydantic models and analytical helpers with concise docstrings describing domain context.

## Testing Guidelines
Pytest drives validation; place files as `tests/<module>/test_<feature>.py`. Mock outbound requests and reuse fixtures defined near consumers to keep runs deterministic. Use parametrized cases to cover yearly rule changes and boundary points. Run `poetry run pytest --maxfail=1 --disable-warnings` before pushing and ensure new CLI options or parsers ship with focused assertions.

## Commit & Pull Request Guidelines
History mixes narrative subjects with Conventional prefixes (`fix: more analysis`), so prefer concise imperative messages and add `feat:`/`fix:` when scope is clear. Isolate scraper logic, analytics, and notebook updates into separate commits. Pull requests should include a summary, test evidence (`poetry run pytest` output or equivalent), related issue links, and screenshots or sample CLI output whenever analytics formatting changes. Request review and wait for CI or local checks to finish before merging.

## Data Coverage Notes
- NM Janitsjar was cancelled in 2020 and 2021 because of the COVID-19 pandemic. The source site (nmjanitsjar.no) does not publish placements for those seasons, so our processed dataset has deliberate gaps for those years.
