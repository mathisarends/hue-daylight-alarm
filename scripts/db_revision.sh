#!/usr/bin/env bash
# Usage: scripts/db_revision.sh "message"
set -euo pipefail
cd "$(dirname "$0")/.."
alembic revision --autogenerate -m "${1:?message required}"
