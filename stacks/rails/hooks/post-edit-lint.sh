#!/usr/bin/env bash
# Post-edit hook: Lint edited Ruby files with rubocop (report only, no auto-fix)
#
# This hook runs after an agent edits a Ruby file. It reports any rubocop
# violations without modifying the files. Use this to verify code quality
# without changing the agent's output.
#
# Usage: Called automatically by the agent system after file edits.
#        Can also be run manually:
#        ./hooks/post-edit-lint.sh path/to/file.rb [path/to/other.rb ...]

set -euo pipefail

# Collect only Ruby files from arguments
ruby_files=()
for file in "$@"; do
  if [[ "$file" == *.rb ]]; then
    ruby_files+=("$file")
  fi
done

# Exit early if no Ruby files were edited
if [[ ${#ruby_files[@]} -eq 0 ]]; then
  exit 0
fi

echo "==> Linting ${#ruby_files[@]} Ruby file(s) with rubocop..."

# Run rubocop in lint-only mode (no auto-correct)
if bundle exec rubocop --force-exclusion --format simple "${ruby_files[@]}"; then
  echo "==> Lint passed. Zero offenses."
else
  exit_code=$?
  echo ""
  echo "==> Lint FAILED. Fix the above offenses before proceeding."
  echo "    Run 'bundle exec rubocop -A ${ruby_files[*]}' to auto-fix safe violations."
  exit $exit_code
fi
