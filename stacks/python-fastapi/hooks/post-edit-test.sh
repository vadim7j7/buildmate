#!/usr/bin/env bash
# Post-edit hook: Run pytest tests related to edited Python files
#
# This hook runs after an agent edits Python files. It determines the
# corresponding test files and runs them. If a test file itself was
# edited, it runs that test directly.
#
# Mapping logic:
#   src/app/routers/projects.py     -> tests/routers/test_projects.py
#   src/app/services/project_service.py -> tests/services/test_project_service.py
#   src/app/models/project.py       -> tests/models/test_project.py
#   src/app/schemas/project.py      -> tests/schemas/test_project.py
#   src/app/tasks/sync.py           -> tests/tasks/test_sync.py
#   tests/**/test_*.py              -> run directly
#
# Usage: Called automatically by the agent system after file edits.
#        Can also be run manually:
#        ./hooks/post-edit-test.sh path/to/file.py [path/to/other.py ...]

set -euo pipefail

# Collect test files to run
test_files=()

for file in "$@"; do
  # Skip non-Python files
  if [[ "$file" != *.py ]]; then
    continue
  fi

  # If it is already a test file, add it directly
  if [[ "$file" == test_*.py || "$file" == */test_*.py ]]; then
    if [[ -f "$file" ]]; then
      test_files+=("$file")
    fi
    continue
  fi

  # Map source file to test file
  test_file=""

  if [[ "$file" == src/app/routers/* ]]; then
    # src/app/routers/projects.py -> tests/routers/test_projects.py
    relative="${file#src/app/routers/}"
    test_file="tests/routers/test_${relative}"

  elif [[ "$file" == src/app/services/* ]]; then
    # src/app/services/project_service.py -> tests/services/test_project_service.py
    relative="${file#src/app/services/}"
    test_file="tests/services/test_${relative}"

  elif [[ "$file" == src/app/models/* ]]; then
    # src/app/models/project.py -> tests/models/test_project.py
    relative="${file#src/app/models/}"
    test_file="tests/models/test_${relative}"

  elif [[ "$file" == src/app/schemas/* ]]; then
    # src/app/schemas/project.py -> tests/schemas/test_project.py
    relative="${file#src/app/schemas/}"
    test_file="tests/schemas/test_${relative}"

  elif [[ "$file" == src/app/tasks/* ]]; then
    # src/app/tasks/sync.py -> tests/tasks/test_sync.py
    relative="${file#src/app/tasks/}"
    test_file="tests/tasks/test_${relative}"
  fi

  # Add the test file if it exists
  if [[ -n "$test_file" && -f "$test_file" ]]; then
    test_files+=("$test_file")
  fi
done

# Remove duplicates
if [[ ${#test_files[@]} -gt 0 ]]; then
  mapfile -t test_files < <(printf '%s\n' "${test_files[@]}" | sort -u)
fi

# Exit early if no test files found
if [[ ${#test_files[@]} -eq 0 ]]; then
  echo "==> No matching test files found for edited files. Skipping test run."
  exit 0
fi

echo "==> Running ${#test_files[@]} test file(s)..."
for f in "${test_files[@]}"; do
  echo "    - $f"
done
echo ""

# Run the matched test files
if uv run pytest "${test_files[@]}" -v --tb=short; then
  echo ""
  echo "==> All tests passed."
else
  exit_code=$?
  echo ""
  echo "==> Some tests FAILED. Review the output above."
  exit $exit_code
fi
