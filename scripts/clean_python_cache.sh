#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
delete=false
assume_yes=false

usage() {
    echo "Usage: scripts/clean_python_cache.sh [--delete] [--yes]"
    echo
    echo "Without --delete, only shows Python cache files that would be removed."
    echo "With --delete, asks for confirmation before removing them."
    echo "With --delete --yes, skips the confirmation prompt."
}

for arg in "$@"; do
    case "$arg" in
        --delete) delete=true ;;
        --yes) assume_yes=true ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if $assume_yes && ! $delete; then
    echo "--yes requires --delete." >&2
    exit 2
fi

declare -a targets=()
while IFS= read -r -d '' target; do
    targets+=("$target")
done < <(
    find "$repo_root" \
        \( -path "$repo_root/.git" -o -path "$repo_root/.venv" -o \
           -path "$repo_root/venv" -o -path "$repo_root/env" -o \
           -path "$repo_root/.cache" -o -path "$repo_root/.pytest_cache" -o \
           -path "$repo_root/.ruff_cache" -o -path '*/node_modules' \) -prune -o \
        \( -type d -name __pycache__ -print0 -prune \) -o \
        \( -type f \( -name '*.pyc' -o -name '*.pyo' \) -print0 \)
)

if ((${#targets[@]} == 0)); then
    echo "No Python cache files found."
    exit 0
fi

echo "Python cache targets in $repo_root:"
for target in "${targets[@]}"; do
    echo "  ${target#"$repo_root"/}"
done
echo
echo "Found ${#targets[@]} target(s)."

if ! $delete; then
    echo "Preview only. Run with --delete to remove these targets."
    exit 0
fi

if ! $assume_yes; then
    read -r -p "Type 'yes' to permanently delete these cache targets: " answer
    if [[ "$answer" != "yes" ]]; then
        echo "Cancelled; nothing was deleted."
        exit 0
    fi
fi

for target in "${targets[@]}"; do
    case "$target" in
        "$repo_root"/*/__pycache__|"$repo_root"/*.pyc|"$repo_root"/*.pyo)
            rm -rf -- "$target"
            ;;
        *)
            echo "Refusing unexpected target: $target" >&2
            exit 1
            ;;
    esac
done

echo "Removed ${#targets[@]} Python cache target(s)."
