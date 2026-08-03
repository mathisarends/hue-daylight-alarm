#!/usr/bin/env bash
# Regenerates the typed API client the CLI is built on, from the FastAPI
# app's own OpenAPI schema. Run this after changing any router or schema.
set -euo pipefail
cd "$(dirname "$0")/.."

uv run python scripts/export_openapi.py

uvx openapi-python-client generate \
  --path openapi.json \
  --meta none \
  --overwrite \
  --output-path cli/src/huerise_cli/generated

rm -f openapi.json
rm -rf cli/src/huerise_cli/generated/.ruff_cache
