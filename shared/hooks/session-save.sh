#!/usr/bin/env bash
# =============================================================================
# session-save.sh — Saves session context on Stop event
# =============================================================================
# Triggered by the "Stop" hook event (fires after each Claude response).
# Gathers git state, in-progress feature files, and pipeline state, then
# writes everything to .claude/context/active-work.md so the next session
# can pick up where this one left off.
#
# Input (stdin): JSON with session_id, cwd, etc.
# Output (stdout): nothing (informational only)
# Exit 0: always (never blocks)
# =============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Parse input
# ---------------------------------------------------------------------------
INPUT="$(cat)"
CWD="$(echo "${INPUT}" | jq -r '.cwd // empty' 2>/dev/null || true)"

if [[ -z "${CWD}" ]]; then
  exit 0
fi

CONTEXT_DIR="${CWD}/.claude/context"
ACTIVE_WORK="${CONTEXT_DIR}/active-work.md"

# Only run if .claude/context/ exists (i.e., this is a bootstrapped project)
if [[ ! -d "${CONTEXT_DIR}" ]]; then
  exit 0
fi

# ---------------------------------------------------------------------------
# Gather context
# ---------------------------------------------------------------------------
TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
BRANCH="$(cd "${CWD}" && git branch --show-current 2>/dev/null || echo 'unknown')"

# Recent commits (last 5 on current branch)
RECENT_COMMITS="$(cd "${CWD}" && git log --oneline -5 2>/dev/null || echo 'none')"

# Uncommitted changes summary
UNCOMMITTED="$(cd "${CWD}" && git diff --stat HEAD 2>/dev/null || echo 'none')"
STAGED="$(cd "${CWD}" && git diff --cached --stat 2>/dev/null || echo 'none')"
UNTRACKED="$(cd "${CWD}" && git ls-files --others --exclude-standard 2>/dev/null | head -20 || echo 'none')"

# In-progress feature files
FEATURES_DIR="${CONTEXT_DIR}/features"
IN_PROGRESS_FEATURES=""
if [[ -d "${FEATURES_DIR}" ]]; then
  for f in "${FEATURES_DIR}"/*.md; do
    [[ -f "${f}" ]] || continue
    if grep -qi 'in.progress\|in_progress' "${f}" 2>/dev/null; then
      FEATURE_NAME="$(basename "${f}")"
      FEATURE_TITLE="$(head -5 "${f}" | grep -m1 '^#' | sed 's/^#\+\s*//' || echo "${FEATURE_NAME}")"
      IN_PROGRESS_FEATURES="${IN_PROGRESS_FEATURES}  - ${FEATURE_TITLE} (${FEATURE_NAME})\n"
    fi
  done
fi

# Pipeline state
PIPELINE_STATE=""
PIPELINE_DIR="${CWD}/.agent-pipeline"
if [[ -d "${PIPELINE_DIR}" && -f "${PIPELINE_DIR}/pipeline.json" ]]; then
  PIPELINE_STATE="$(cat "${PIPELINE_DIR}/pipeline.json" 2>/dev/null || echo '')"
fi

# ---------------------------------------------------------------------------
# Write active-work.md
# ---------------------------------------------------------------------------
cat > "${ACTIVE_WORK}" <<WORKFILE
# Active Work Context

> Auto-saved at ${TIMESTAMP}

## Branch
\`${BRANCH}\`

## Recent Commits
\`\`\`
${RECENT_COMMITS}
\`\`\`

## Uncommitted Changes
### Staged
\`\`\`
${STAGED}
\`\`\`

### Unstaged
\`\`\`
${UNCOMMITTED}
\`\`\`

### Untracked Files
\`\`\`
${UNTRACKED}
\`\`\`

## In-Progress Features
$(if [[ -n "${IN_PROGRESS_FEATURES}" ]]; then echo -e "${IN_PROGRESS_FEATURES}"; else echo "None"; fi)

## Pipeline State
$(if [[ -n "${PIPELINE_STATE}" ]]; then echo "\`\`\`json"; echo "${PIPELINE_STATE}"; echo "\`\`\`"; else echo "No active pipeline"; fi)
WORKFILE

exit 0
