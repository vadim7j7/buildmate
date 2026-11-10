#!/bin/bash
# Session Start Hook (SessionStart)
# Prints the context saved at the end of the previous session. Claude Code adds
# a SessionStart hook's stdout to the conversation, so the new session starts
# knowing the branch, uncommitted changes and in-progress features.
# Also marks the session start in the activity log, so session-end.sh can count
# only this session's activity.

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
CONTEXT_DIR="$PROJECT_ROOT/.claude/context"
ACTIVE_WORK_FILE="$CONTEXT_DIR/active-work.md"
ACTIVITY_LOG="$CONTEXT_DIR/agent-activity.log"

INPUT=$(cat 2>/dev/null) || INPUT="{}"
SESSION_ID="unknown"
if command -v jq &> /dev/null; then
    SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null) || SESSION_ID="unknown"
fi

mkdir -p "$CONTEXT_DIR" 2>/dev/null || exit 0
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null) || TIMESTAMP="unknown"
echo "[$TIMESTAMP] Session started: $SESSION_ID" >> "$ACTIVITY_LOG" 2>/dev/null

if [ -f "$ACTIVE_WORK_FILE" ]; then
    echo "Context saved at the end of the previous session (.claude/context/active-work.md):"
    echo
    head -60 "$ACTIVE_WORK_FILE"
    echo
    echo "Run /recap for the full picture (feature files, pipeline status)."
fi

exit 0
