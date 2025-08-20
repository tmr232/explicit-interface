# https://just.systems

set windows-shell := ["pwsh", "-c"]

@_:
    just --list

@format:
    uv run ruff check --fix .
    uv run ruff format .

# Run tests
@test:
    uv run pytest tests