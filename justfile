default:
    @just --list

install:
    uv sync --all-extras

test:
    uv run pytest -vv tests/

lint:
    uv run ruff check .

lint-fix:
    uv run ruff check --fix .

format:
    uv run ruff format .

check: lint test

codebase-text-dump:
	rm -f tulip-codebase.txt
	uv run gitingest -o tulip-codebase.txt -e .venv -e uv.lock
