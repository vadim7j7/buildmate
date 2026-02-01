#!/usr/bin/env bash
# =============================================================================
# session-load.sh — Loads session context on SessionStart event
# =============================================================================
# Triggered by the "SessionStart" hook event. Reads .claude/context/active-work.md
# and outputs it to stdout so Claude Code injects it into the conversation context.
#
# Input (stdin): JSON with session_id, cwd, etc.
# Output (stdout): context text (injected into conversation)
# Exit 0: always
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

ACTIVE_WORK="${CWD}/.claude/context/active-work.md"

# Only output if the file exists and is non-empty
if [[ ! -s "${ACTIVE_WORK}" ]]; then
  exit 0
fi

# ---------------------------------------------------------------------------
# Check if context is stale (older than 7 days)
# ---------------------------------------------------------------------------
if command -v stat &>/dev/null; then
  if [[ "$(uname)" == "Darwin" ]]; then
    FILE_EPOCH="$(stat -f '%m' "${ACTIVE_WORK}" 2>/dev/null || echo 0)"
  else
    FILE_EPOCH="$(stat -c '%Y' "${ACTIVE_WORK}" 2>/dev/null || echo 0)"
  fi
  NOW_EPOCH="$(date +%s)"
  AGE_DAYS="$(( (NOW_EPOCH - FILE_EPOCH) / 86400 ))"

  if [[ "${AGE_DAYS}" -gt 7 ]]; then
    echo "[Session Memory] Previous work context is ${AGE_DAYS} days old and may be stale. Use /resume for a fresh assessment."
    exit 0
  fi
fi

# ---------------------------------------------------------------------------
# Output context for injection
# ---------------------------------------------------------------------------
echo "[Session Memory] Loading context from previous session:"
echo ""
cat "${ACTIVE_WORK}"
echo ""
echo "---"
echo "Use /resume for a detailed status check, or continue working where you left off."

exit 0
