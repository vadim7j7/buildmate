#!/usr/bin/env bash
# Post-edit hook: Lint and type-check edited Python files with ruff + mypy
#
# This hook runs after an agent edits a Python file. It reports any ruff
# lint violations and mypy type errors without modifying the files.
#
# Usage: Called automatically by the agent system after file edits.
#        Can also be run manually:
#        ./hooks/post-edit-lint.sh path/to/file.py [path/to/other.py ...]

set -euo pipefail

# Collect only Python files from arguments
py_files=()
for file in "$@"; do
  if [[ "$file" == *.py ]]; then
    py_files+=("$file")
  fi
done

# Exit early if no Python files were edited
if [[ ${#py_files[@]} -eq 0 ]]; then
  exit 0
fi

overall_exit=0

# Run ruff check (lint)
echo "==> Linting ${#py_files[@]} Python file(s) with ruff check..."

if uv run ruff check "${py_files[@]}"; then
  echo "==> Ruff lint passed. Zero violations."
else
  exit_code=$?
  echo ""
  echo "==> Ruff lint FAILED. Fix the above violations before proceeding."
  echo "    Run 'uv run ruff check --fix ${py_files[*]}' to auto-fix safe violations."
  overall_exit=$exit_code
fi

# Run mypy (type check) - only on src/ files, skip test files
src_files=()
for file in "${py_files[@]}"; do
  if [[ "$file" != tests/* ]]; then
    src_files+=("$file")
  fi
done

if [[ ${#src_files[@]} -gt 0 ]]; then
  echo ""
  echo "==> Type-checking ${#src_files[@]} file(s) with mypy..."

  if uv run mypy "${src_files[@]}"; then
    echo "==> mypy passed. Zero errors."
  else
    exit_code=$?
    echo ""
    echo "==> mypy FAILED. Fix the above type errors before proceeding."
    overall_exit=$exit_code
  fi
fi

exit $overall_exit
