#!/usr/bin/env bash
# cleanup-worktrees.sh -- Remove parallel agent worktrees and their branches.
#
# Usage:
#   ./cleanup-worktrees.sh [worktrees-dir]
#
# Arguments:
#   worktrees-dir   Path to the .agent-worktrees/ directory.
#                   Defaults to <repo-root>/.agent-worktrees/
#
# Exit codes:
#   0  Cleanup successful (or nothing to clean)
#   2  Not a git repository

set -euo pipefail

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: Not inside a git repository." >&2
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKTREES_DIR="${1:-${REPO_ROOT}/.agent-worktrees}"

if [[ ! -d "${WORKTREES_DIR}" ]]; then
  echo "No worktrees directory found. Nothing to clean up."
  exit 0
fi

# ---------------------------------------------------------------------------
# Remove worktrees
# ---------------------------------------------------------------------------

CLEANED=0
ERRORS=0

for worktree in "${WORKTREES_DIR}"/*/; do
  # Skip if not a directory
  [[ -d "${worktree}" ]] || continue

  WORKTREE_PATH="$(cd "${worktree}" && pwd)"
  TASK_NAME="$(basename "${worktree}")"

  echo "Removing worktree: ${TASK_NAME}"

  # Read the branch name before removing the worktree
  BRANCH=""
  STATUS_FILE="${worktree}.agent-status/progress.md"
  if [[ -f "${STATUS_FILE}" ]]; then
    BRANCH="$(grep -i '^**Branch:' "${STATUS_FILE}" 2>/dev/null | head -1 | sed 's/.*Branch:\*\*\s*//' | tr -d '[:space:]' || true)"
  fi

  # Remove the git worktree
  if git worktree remove --force "${WORKTREE_PATH}" 2>/dev/null; then
    CLEANED=$((CLEANED + 1))
  else
    echo "  Warning: Failed to remove worktree via git. Removing directory manually." >&2
    rm -rf "${WORKTREE_PATH}"
    CLEANED=$((CLEANED + 1))
  fi

  # Remove the associated branch if it exists and is not checked out elsewhere
  if [[ -n "${BRANCH}" ]] && git rev-parse --verify "${BRANCH}" &>/dev/null; then
    if git branch -d "${BRANCH}" 2>/dev/null; then
      echo "  Deleted branch: ${BRANCH}"
    else
      echo "  Warning: Could not delete branch ${BRANCH} (may have unmerged changes)." >&2
      ERRORS=$((ERRORS + 1))
    fi
  fi
done

# ---------------------------------------------------------------------------
# Clean up the worktrees directory itself
# ---------------------------------------------------------------------------

# Remove the directory if it is now empty
if [[ -d "${WORKTREES_DIR}" ]]; then
  rmdir "${WORKTREES_DIR}" 2>/dev/null || true
fi

# Prune any stale worktree references
git worktree prune 2>/dev/null || true

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "Cleanup complete. Removed ${CLEANED} worktree(s)."
if [[ ${ERRORS} -gt 0 ]]; then
  echo "Warnings: ${ERRORS} branch(es) could not be deleted (may need manual cleanup)."
fi

exit 0
