.PHONY: test lint lint-fix format format-check openapi

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

lint-fix:
	uv run ruff check --fix .
	uv run ruff format .

format: lint-fix

format-check:
	uv run ruff format --check .

openapi:
	uv run python scripts/export_openapi.py
