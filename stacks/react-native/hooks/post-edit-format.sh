#!/usr/bin/env bash
# post-edit-format.sh
# Runs Prettier on files that were just edited by an agent.
# Called automatically after file edits to maintain consistent formatting.
#
# Usage: post-edit-format.sh <file1> [file2] [file3] ...
# Exit codes: 0 = success, 1 = prettier not found, 2 = formatting failed

set -euo pipefail

if [ $# -eq 0 ]; then
  echo "[post-edit-format] No files provided, skipping."
  exit 0
fi

# Check that prettier is available
if ! command -v npx &>/dev/null; then
  echo "[post-edit-format] npx not found, skipping formatting."
  exit 1
fi

# Filter to only TypeScript/JavaScript/JSON files that exist
FILES_TO_FORMAT=()
for file in "$@"; do
  if [ -f "$file" ]; then
    case "$file" in
      *.ts|*.tsx|*.js|*.jsx|*.json|*.css|*.md)
        FILES_TO_FORMAT+=("$file")
        ;;
    esac
  fi
done

if [ ${#FILES_TO_FORMAT[@]} -eq 0 ]; then
  echo "[post-edit-format] No formattable files found, skipping."
  exit 0
fi

echo "[post-edit-format] Formatting ${#FILES_TO_FORMAT[@]} file(s)..."

# Run prettier on the specific files
if npx prettier --write "${FILES_TO_FORMAT[@]}" 2>/dev/null; then
  echo "[post-edit-format] Formatting complete."
else
  echo "[post-edit-format] Prettier formatting failed for some files."
  exit 2
fi
