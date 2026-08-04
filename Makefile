.PHONY: build fmt test vet generate check-generated

build:
	mkdir -p bin
	go -C cli build -o ../bin/huerise ./cmd/huerise

fmt:
	go -C cli fmt ./cmd/... ./internal/...

test:
	go -C cli test ./...

vet:
	go -C cli vet ./...

generate:
	uv run python scripts/export_openapi.py
	cp openapi.json cli/openapi.json
	go -C cli generate ./internal/generate

check-generated: generate
	git diff --exit-code -- openapi.json cli/internal/client
