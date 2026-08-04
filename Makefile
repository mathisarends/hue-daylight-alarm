.PHONY: build fmt test vet generate check-generated

build:
	mkdir -p bin
	go build -o bin/huerise ./cmd/huerise

fmt:
	go fmt ./cmd/... ./internal/...

test:
	go test ./...

vet:
	go vet ./...

generate:
	uv run python scripts/export_openapi.py
	go generate ./internal/generate

check-generated: generate
	git diff --exit-code -- openapi.json internal/api
