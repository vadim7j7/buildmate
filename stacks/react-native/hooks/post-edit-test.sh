#!/usr/bin/env bash
# post-edit-test.sh
# Runs Jest for test files that were just edited, or finds related tests
# for edited source files.
#
# Usage: post-edit-test.sh <file1> [file2] [file3] ...
# Exit codes: 0 = tests pass, 1 = jest not found, 2 = tests failed

set -euo pipefail

if [ $# -eq 0 ]; then
  echo "[post-edit-test] No files provided, skipping."
  exit 0
fi

# Check that npx is available
if ! command -v npx &>/dev/null; then
  echo "[post-edit-test] npx not found, skipping tests."
  exit 1
fi

# Collect test files to run
TEST_FILES=()
for file in "$@"; do
  if [ ! -f "$file" ]; then
    continue
  fi

  case "$file" in
    # If the edited file IS a test file, run it directly
    *.test.ts|*.test.tsx|*.spec.ts|*.spec.tsx)
      TEST_FILES+=("$file")
      ;;
    # If the edited file is a source file, find its corresponding test
    *.ts|*.tsx)
      # Derive the base name without extension
      basename=$(basename "$file" | sed 's/\.\(ts\|tsx\)$//')
      dirname=$(dirname "$file")

      # Look for test files in common locations
      for test_pattern in \
        "__tests__/**/${basename}.test.tsx" \
        "__tests__/**/${basename}.test.ts" \
        "${dirname}/__tests__/${basename}.test.tsx" \
        "${dirname}/__tests__/${basename}.test.ts" \
        "${dirname}/${basename}.test.tsx" \
        "${dirname}/${basename}.test.ts"; do
        # Use find to locate matching files (glob patterns)
        while IFS= read -r -d '' found_test; do
          TEST_FILES+=("$found_test")
        done < <(find . -path "./$test_pattern" -print0 2>/dev/null || true)
      done
      ;;
  esac
done

# Deduplicate test files
if [ ${#TEST_FILES[@]} -gt 0 ]; then
  UNIQUE_TESTS=($(printf '%s\n' "${TEST_FILES[@]}" | sort -u))
else
  echo "[post-edit-test] No related test files found, skipping."
  exit 0
fi

echo "[post-edit-test] Running ${#UNIQUE_TESTS[@]} test file(s)..."

# Run jest with the specific test files
if npx jest --bail --no-coverage "${UNIQUE_TESTS[@]}" 2>&1; then
  echo "[post-edit-test] All tests passed."
else
  JEST_EXIT=$?
  echo "[post-edit-test] Some tests failed (exit code: $JEST_EXIT)."
  exit 2
fi
