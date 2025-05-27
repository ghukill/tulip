default:
    @just --list

install:
    uv sync --all-extras

test:
    uv run pytest -vv tests/

lint:
    uv run ruff check .

format:
    uv run ruff format .

check: lint test