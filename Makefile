.PHONY: build fmt test vet generate check-generated lint lint-fix format format-check

build:
	mkdir -p bin
	go -C cli build -o ../bin/huerise ./cmd/huerise

fmt:
	go -C cli fmt ./cmd/... ./internal/...

test:
	go -C cli test ./...

vet:
	go -C cli vet ./...

lint:
	uv run --group dev ruff check .
	uv run --group dev ruff format --check .

lint-fix:
	uv run --group dev ruff check --fix .
	uv run --group dev ruff format .

format: lint-fix

format-check:
	uv run --group dev ruff format --check .

generate:
	uv run python scripts/export_openapi.py
	cp openapi.json cli/openapi.json
	go -C cli generate ./internal/generate

check-generated: generate
	git diff --exit-code -- openapi.json cli/internal/client
