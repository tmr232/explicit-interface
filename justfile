# https://just.systems

set windows-shell := ["pwsh", "-c"]

@default:
    just --summary


@format:
    ruff check --fix .
    ruff format .

@test:
    pytest tests