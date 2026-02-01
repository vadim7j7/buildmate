#!/usr/bin/env bash
# post-edit-lint.sh
# Runs ESLint on files that were just edited by an agent.
# Called automatically after file edits to catch lint violations early.
#
# Usage: post-edit-lint.sh <file1> [file2] [file3] ...
# Exit codes: 0 = no errors, 1 = eslint not found, 2 = lint errors found

set -euo pipefail

if [ $# -eq 0 ]; then
  echo "[post-edit-lint] No files provided, skipping."
  exit 0
fi

# Check that npx is available
if ! command -v npx &>/dev/null; then
  echo "[post-edit-lint] npx not found, skipping lint."
  exit 1
fi

# Filter to only TypeScript/JavaScript files that exist
FILES_TO_LINT=()
for file in "$@"; do
  if [ -f "$file" ]; then
    case "$file" in
      *.ts|*.tsx|*.js|*.jsx)
        FILES_TO_LINT+=("$file")
        ;;
    esac
  fi
done

if [ ${#FILES_TO_LINT[@]} -eq 0 ]; then
  echo "[post-edit-lint] No lintable files found, skipping."
  exit 0
fi

echo "[post-edit-lint] Linting ${#FILES_TO_LINT[@]} file(s)..."

# Run eslint on the specific files
# Use --no-error-on-unmatched-pattern to handle cases where files are filtered by eslint config
if npx eslint --no-error-on-unmatched-pattern "${FILES_TO_LINT[@]}" 2>/dev/null; then
  echo "[post-edit-lint] No lint errors found."
else
  LINT_EXIT=$?
  echo "[post-edit-lint] ESLint found issues (exit code: $LINT_EXIT)."
  echo "[post-edit-lint] Run 'npx eslint --fix ${FILES_TO_LINT[*]}' to auto-fix."
  exit 2
fi
