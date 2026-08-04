#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd "$script_dir/.." && pwd)"
cd "$repo_dir"

export AUDIO_BACKENDS=local
exec docker compose -f compose.yml -f compose.audio.yml up --build "$@"
