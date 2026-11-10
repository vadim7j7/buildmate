#!/bin/bash
# Session End Hook (Stop)
# Generates a summary of the session's activity when Claude Code stops.
#
# Input: JSON via stdin with session_id, transcript_path
# Output: Creates .claude/context/session-summary.md

# Don't use set -e - we want to be non-blocking
# Hooks should not fail the main operation

# Find project root by looking for .claude directory
find_project_root() {
    local dir="$PWD"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.claude" ]; then
            echo "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    # Fallback to current directory
    echo "$PWD"
}

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(find_project_root)}"
CONTEXT_DIR="$PROJECT_ROOT/.claude/context"
ACTIVITY_LOG="$CONTEXT_DIR/agent-activity.log"
SUMMARY_FILE="$CONTEXT_DIR/session-summary.md"

# Read JSON input from stdin
INPUT=$(cat 2>/dev/null) || INPUT="{}"

# Extract session info (check if jq is available)
if command -v jq &> /dev/null; then
    SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null) || SESSION_ID="unknown"
else
    SESSION_ID="unknown"
fi
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null) || TIMESTAMP="unknown"

# Ensure context directory exists
mkdir -p "$CONTEXT_DIR" 2>/dev/null || exit 0

# Count activities from this session (if log exists)
if [ -f "$ACTIVITY_LOG" ]; then
    # Only the lines after the last "Session started" marker (see session-start.sh)
    SESSION_LOG=$(awk '/Session started:/ {buf=""; next} {buf = buf $0 "\n"} END {printf "%s", buf}' "$ACTIVITY_LOG" 2>/dev/null)
    FILE_EDITS=$(printf "%b" "$SESSION_LOG" | grep -c "Edit:\|Write:" 2>/dev/null)
    TASKS_COMPLETED=$(printf "%b" "$SESSION_LOG" | grep -c "Task completed:" 2>/dev/null)
    RECENT_CHANGES=$(printf "%b" "$SESSION_LOG" | tail -20)
    [ -z "$RECENT_CHANGES" ] && RECENT_CHANGES="No activity this session"
else
    FILE_EDITS=0
    TASKS_COMPLETED=0
    RECENT_CHANGES="No activity recorded"
fi

# Get git status
GIT_STATUS=$(git -C "$PROJECT_ROOT" status --short 2>/dev/null | head -10 || echo "Not a git repository")
UNCOMMITTED_COUNT=$(git -C "$PROJECT_ROOT" status --short 2>/dev/null | wc -l | tr -d ' ' || echo "0")

# Write session summary
cat > "$SUMMARY_FILE" 2>/dev/null << EOF
# Session Summary

**Session ID:** $SESSION_ID
**Ended:** $TIMESTAMP

## Activity Summary

- **Files edited:** $FILE_EDITS
- **Agent tasks completed:** $TASKS_COMPLETED
- **Uncommitted changes:** $UNCOMMITTED_COUNT files

## Recent Activity

\`\`\`
$RECENT_CHANGES
\`\`\`

## Git Status

\`\`\`
$GIT_STATUS
\`\`\`
EOF

exit 0
