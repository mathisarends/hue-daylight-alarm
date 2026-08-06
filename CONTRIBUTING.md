# Contributing

## Prerequisites

- Python 3.14+ and [`uv`](https://docs.astral.sh/uv/)
- Go 1.25+ for the CLI
- Docker and Docker Compose for running the full stack

## Setup

```bash
uv sync --all-extras
uv run python -m huerise.main
```

## Checks

Run these before opening a pull request:

```bash
uv run --all-extras pytest
uvx ruff check .
go -C cli test ./...
go -C cli vet ./...
```

If you changed an API route or schema, regenerate the OpenAPI document and the
Go client, then verify nothing is out of sync:

```bash
make generate
make check-generated
```

Do not edit generated client files in `cli/internal/client/` by hand.

## Commit style

Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
(`feat:`, `fix:`, `docs:`, `chore:`, ...). Keep commits small and focused on
one change.

## Pull requests

Describe what changed and why. Link any related issue. Make sure the checks
above pass before requesting review.
