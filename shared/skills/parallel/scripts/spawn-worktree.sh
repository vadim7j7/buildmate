#!/usr/bin/env bash
# spawn-worktree.sh -- Create a git worktree for parallel agent work.
#
# Usage:
#   ./spawn-worktree.sh <task-slug>
#
# Arguments:
#   task-slug   A short, URL-safe identifier for the task (e.g., "login-page")
#
# Output:
#   Prints the absolute path to the created worktree on stdout.
#
# Exit codes:
#   0  Success
#   1  Invalid arguments
#   2  Not a git repository
#   3  Worktree creation failed

set -euo pipefail

# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <task-slug>" >&2
  exit 1
fi

TASK_SLUG="$1"

# ---------------------------------------------------------------------------
# Validate git repository
# ---------------------------------------------------------------------------

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: Not inside a git repository." >&2
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
TIMESTAMP="$(date +%Y%m%d%H%M%S)"
WORKTREE_BRANCH="agent-parallel/${TIMESTAMP}-${TASK_SLUG}"
WORKTREE_DIR="${REPO_ROOT}/.agent-worktrees/${TIMESTAMP}-${TASK_SLUG}"

# ---------------------------------------------------------------------------
# Create worktree
# ---------------------------------------------------------------------------

# Ensure the parent directory exists
mkdir -p "${REPO_ROOT}/.agent-worktrees"

# Create a new worktree with a new branch from the current HEAD
if ! git worktree add -b "${WORKTREE_BRANCH}" "${WORKTREE_DIR}" HEAD 2>/dev/null; then
  echo "Error: Failed to create worktree at ${WORKTREE_DIR}" >&2
  exit 3
fi

# ---------------------------------------------------------------------------
# Set up worktree environment
# ---------------------------------------------------------------------------

# Copy .claude/ configuration if it exists in the repo root
if [[ -d "${REPO_ROOT}/.claude" ]]; then
  cp -r "${REPO_ROOT}/.claude" "${WORKTREE_DIR}/.claude"
fi

# Create the agent status directory for progress tracking
mkdir -p "${WORKTREE_DIR}/.agent-status"

# Write initial status
cat > "${WORKTREE_DIR}/.agent-status/progress.md" <<EOF
# Agent Status

**Task:** ${TASK_SLUG}
**Branch:** ${WORKTREE_BRANCH}
**Parent Branch:** ${CURRENT_BRANCH}
**Started:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Status:** RUNNING
EOF

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

echo "${WORKTREE_DIR}"
