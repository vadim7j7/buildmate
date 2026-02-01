#!/usr/bin/env bash
# Post-edit hook: Auto-format edited Ruby files with rubocop -A
#
# This hook runs after an agent edits a Ruby file. It auto-corrects
# safe rubocop violations (formatting, whitespace, style) without
# changing semantics.
#
# Usage: Called automatically by the agent system after file edits.
#        Can also be run manually:
#        ./hooks/post-edit-format.sh path/to/file.rb [path/to/other.rb ...]

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

echo "==> Auto-formatting ${#ruby_files[@]} Ruby file(s) with rubocop -A..."

# Run rubocop auto-correct (safe corrections only)
if bundle exec rubocop -A --force-exclusion "${ruby_files[@]}" 2>/dev/null; then
  echo "==> Formatting complete. All files clean."
else
  exit_code=$?
  if [[ $exit_code -eq 1 ]]; then
    # Exit code 1 means offenses were found but some could not be auto-corrected
    echo "==> Warning: Some offenses could not be auto-corrected. Run 'bundle exec rubocop' for details."
  else
    echo "==> Error: rubocop failed with exit code $exit_code"
    exit $exit_code
  fi
fi
