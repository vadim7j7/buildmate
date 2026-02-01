#!/usr/bin/env bash
# post-edit-test.sh
# Runs Jest tests related to edited files.
#
# Usage: Called automatically by the agent framework after file edits.
# Expects file paths as arguments.
#
# Only runs tests for files that have corresponding test files or are
# test files themselves.

set -euo pipefail

SUPPORTED_EXTENSIONS="ts|tsx|js|jsx"

test_files=()

for file in "$@"; do
  if [[ ! -f "$file" ]]; then
    continue
  fi

  extension="${file##*.}"
  if [[ ! "$extension" =~ ^($SUPPORTED_EXTENSIONS)$ ]]; then
    continue
  fi

  # If this is already a test file, add it
  if [[ "$file" =~ \.(test|spec)\.(ts|tsx|js|jsx)$ ]]; then
    test_files+=("$file")
    continue
  fi

  # Look for a co-located test file
  base="${file%.*}"
  for test_ext in "test.tsx" "test.ts" "spec.tsx" "spec.ts" "test.js" "test.jsx" "spec.js" "spec.jsx"; do
    test_candidate="${base}.${test_ext}"
    if [[ -f "$test_candidate" ]]; then
      test_files+=("$test_candidate")
      break
    fi
  done
done

if [[ ${#test_files[@]} -eq 0 ]]; then
  echo "--- No related test files found. Skipping tests. ---"
  exit 0
fi

# Deduplicate test files
readarray -t unique_tests < <(printf '%s\n' "${test_files[@]}" | sort -u)

# Check if jest is available
if command -v npx &> /dev/null && { [[ -f "node_modules/.bin/jest" ]] || [[ -f "node_modules/.bin/vitest" ]]; }; then
  echo "--- Running ${#unique_tests[@]} test file(s) ---"

  if [[ -f "node_modules/.bin/jest" ]]; then
    npx jest "${unique_tests[@]}" --passWithNoTests 2>&1 || {
      echo "--- Tests failed. Please fix before proceeding. ---"
      exit 1
    }
  elif [[ -f "node_modules/.bin/vitest" ]]; then
    npx vitest run "${unique_tests[@]}" 2>&1 || {
      echo "--- Tests failed. Please fix before proceeding. ---"
      exit 1
    }
  fi

  echo "--- Tests passed ---"
else
  echo "--- Test runner not found. Skipping tests. ---"
fi
