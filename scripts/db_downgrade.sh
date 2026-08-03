#!/usr/bin/env bash
# Usage: scripts/db_downgrade.sh [target]  (default: -1)
set -euo pipefail
cd "$(dirname "$0")/.."
alembic downgrade "${1:--1}"
