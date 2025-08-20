# https://just.systems

set windows-shell := ["pwsh", "-c"]

@_:
    just --list

@format:
    uv run ruff check --fix .
    uv run ruff format .

@lint: format
    uv run mypy .

@ci:
    uv run ruff check .
    uv run ruff format --check .
    uv run mypy .

# Run tests
@test *args:
    uv run pytest tests {{args}}