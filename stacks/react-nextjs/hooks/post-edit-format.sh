#!/usr/bin/env bash
# post-edit-format.sh
# Runs Prettier on files after they are edited by an agent.
#
# Usage: Called automatically by the agent framework after file edits.
# Expects file paths as arguments.
#
# This hook formats TypeScript, TSX, JavaScript, JSX, CSS, and JSON files
# using the project's Prettier configuration.

set -euo pipefail

# Only process supported file types
SUPPORTED_EXTENSIONS="ts|tsx|js|jsx|css|json|md"

files_to_format=()

for file in "$@"; do
  if [[ -f "$file" ]]; then
    extension="${file##*.}"
    if [[ "$extension" =~ ^($SUPPORTED_EXTENSIONS)$ ]]; then
      files_to_format+=("$file")
    fi
  fi
done

if [[ ${#files_to_format[@]} -eq 0 ]]; then
  exit 0
fi

# Check if prettier is available
if command -v npx &> /dev/null && [[ -f "node_modules/.bin/prettier" ]]; then
  npx prettier --write "${files_to_format[@]}" 2>/dev/null || true
elif command -v prettier &> /dev/null; then
  prettier --write "${files_to_format[@]}" 2>/dev/null || true
fi
