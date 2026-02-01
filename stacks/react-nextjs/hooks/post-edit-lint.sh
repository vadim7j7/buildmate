#!/usr/bin/env bash
# post-edit-lint.sh
# Runs ESLint on files after they are edited by an agent.
#
# Usage: Called automatically by the agent framework after file edits.
# Expects file paths as arguments.
#
# Reports lint errors and warnings. Does NOT auto-fix by default --
# agents should fix issues manually to ensure intentional changes.

set -euo pipefail

# Only lint TypeScript and JavaScript files
SUPPORTED_EXTENSIONS="ts|tsx|js|jsx"

files_to_lint=()

for file in "$@"; do
  if [[ -f "$file" ]]; then
    extension="${file##*.}"
    if [[ "$extension" =~ ^($SUPPORTED_EXTENSIONS)$ ]]; then
      files_to_lint+=("$file")
    fi
  fi
done

if [[ ${#files_to_lint[@]} -eq 0 ]]; then
  exit 0
fi

# Check if eslint is available
if command -v npx &> /dev/null && [[ -f "node_modules/.bin/eslint" ]]; then
  echo "--- Linting ${#files_to_lint[@]} file(s) ---"
  npx eslint "${files_to_lint[@]}" --no-error-on-unmatched-pattern 2>&1 || {
    echo "--- Lint issues found. Please fix before proceeding. ---"
    exit 1
  }
  echo "--- Lint passed ---"
elif [[ -f "node_modules/.bin/next" ]]; then
  # Fall back to next lint if eslint is not directly available
  echo "--- Running next lint ---"
  npx next lint 2>&1 || {
    echo "--- Lint issues found. Please fix before proceeding. ---"
    exit 1
  }
  echo "--- Lint passed ---"
else
  echo "--- ESLint not found. Skipping lint. ---"
fi
