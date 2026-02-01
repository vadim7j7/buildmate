#!/usr/bin/env bash
# Post-edit hook: Auto-format edited Python files with ruff format
#
# This hook runs after an agent edits a Python file. It auto-formats
# the file using ruff, which applies consistent code style (PEP 8,
# line length, import sorting) without changing semantics.
#
# Usage: Called automatically by the agent system after file edits.
#        Can also be run manually:
#        ./hooks/post-edit-format.sh path/to/file.py [path/to/other.py ...]

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

echo "==> Formatting ${#py_files[@]} Python file(s) with ruff format..."

# Run ruff format
if uv run ruff format "${py_files[@]}" 2>/dev/null; then
  echo "==> Formatting complete. All files clean."
else
  exit_code=$?
  echo "==> Error: ruff format failed with exit code $exit_code"
  exit $exit_code
fi
