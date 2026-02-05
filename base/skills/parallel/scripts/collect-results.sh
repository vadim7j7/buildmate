#!/usr/bin/env bash
# collect-results.sh -- Collect results from parallel agent worktrees.
#
# Usage:
#   ./collect-results.sh [worktrees-dir]
#
# Arguments:
#   worktrees-dir   Path to the .agent-worktrees/ directory.
#                   Defaults to <repo-root>/.agent-worktrees/
#
# Output:
#   Prints an aggregated Markdown report to stdout.
#
# Exit codes:
#   0  All tasks succeeded
#   1  One or more tasks failed
#   2  Not a git repository

set -euo pipefail

# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: Not inside a git repository." >&2
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKTREES_DIR="${1:-${REPO_ROOT}/.agent-worktrees}"

if [[ ! -d "${WORKTREES_DIR}" ]]; then
  echo "Error: Worktrees directory not found: ${WORKTREES_DIR}" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Collect results
# ---------------------------------------------------------------------------

TOTAL=0
SUCCEEDED=0
FAILED=0
RESULTS=""

for worktree in "${WORKTREES_DIR}"/*/; do
  # Skip if not a directory
  [[ -d "${worktree}" ]] || continue

  TOTAL=$((TOTAL + 1))
  TASK_NAME="$(basename "${worktree}")"
  STATUS_FILE="${worktree}.agent-status/progress.md"
  RESULT_FILE="${worktree}.agent-status/result.md"

  # Determine task status
  if [[ -f "${RESULT_FILE}" ]]; then
    # Read the status from the result file
    TASK_STATUS="$(grep -i 'status:' "${RESULT_FILE}" | head -1 | sed 's/.*Status:\s*//' | tr -d '[:space:]' || echo "UNKNOWN")"
  elif [[ -f "${STATUS_FILE}" ]]; then
    TASK_STATUS="$(grep -i 'status:' "${STATUS_FILE}" | head -1 | sed 's/.*Status:\s*//' | tr -d '[:space:]' || echo "UNKNOWN")"
  else
    TASK_STATUS="UNKNOWN"
  fi

  # Normalise status
  case "${TASK_STATUS}" in
    SUCCESS|COMPLETED|DONE|PASSED)
      SUCCEEDED=$((SUCCEEDED + 1))
      STATUS_DISPLAY="SUCCESS"
      ;;
    FAILED|ERROR|CRASHED)
      FAILED=$((FAILED + 1))
      STATUS_DISPLAY="FAILED"
      ;;
    RUNNING)
      STATUS_DISPLAY="RUNNING"
      ;;
    *)
      FAILED=$((FAILED + 1))
      STATUS_DISPLAY="UNKNOWN"
      ;;
  esac

  # Read the branch name from status
  BRANCH="$(grep -i 'branch:' "${STATUS_FILE}" 2>/dev/null | head -1 | sed 's/.*Branch:\s*//' | tr -d '[:space:]' || echo "N/A")"

  # Build the results table row
  RESULTS="${RESULTS}| ${TASK_NAME} | ${STATUS_DISPLAY} | ${BRANCH} |\n"
done

# ---------------------------------------------------------------------------
# Output report
# ---------------------------------------------------------------------------

cat <<EOF
## Parallel Execution Report

**Tasks:** ${TOTAL}
**Succeeded:** ${SUCCEEDED}
**Failed:** ${FAILED}
**Collected At:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")

### Results

| Task | Status | Branch |
|------|--------|--------|
$(echo -e "${RESULTS}")
EOF

# Print individual result details if they exist
for worktree in "${WORKTREES_DIR}"/*/; do
  [[ -d "${worktree}" ]] || continue

  TASK_NAME="$(basename "${worktree}")"
  RESULT_FILE="${worktree}.agent-status/result.md"

  if [[ -f "${RESULT_FILE}" ]]; then
    echo ""
    echo "---"
    echo ""
    echo "### Details: ${TASK_NAME}"
    echo ""
    cat "${RESULT_FILE}"
  fi
done

# ---------------------------------------------------------------------------
# Exit code
# ---------------------------------------------------------------------------

if [[ ${FAILED} -gt 0 ]]; then
  exit 1
fi

exit 0
