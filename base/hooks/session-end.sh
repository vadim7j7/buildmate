#!/bin/bash
# Session End Hook (Stop)
# Generates a summary of the session's activity when Claude Code stops.
#
# Input: JSON via stdin with session_id, transcript_path
# Output: Creates .claude/context/session-summary.md

set -e

CONTEXT_DIR=".claude/context"
ACTIVITY_LOG="$CONTEXT_DIR/agent-activity.log"
SUMMARY_FILE="$CONTEXT_DIR/session-summary.md"

# Read JSON input from stdin
INPUT=$(cat)

# Extract session info
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Ensure context directory exists
mkdir -p "$CONTEXT_DIR"

# Count activities from this session (if log exists)
if [ -f "$ACTIVITY_LOG" ]; then
    FILE_EDITS=$(grep -c "Edit:\|Write:" "$ACTIVITY_LOG" 2>/dev/null || echo "0")
    TASKS_COMPLETED=$(grep -c "Task completed:" "$ACTIVITY_LOG" 2>/dev/null || echo "0")
    RECENT_CHANGES=$(tail -20 "$ACTIVITY_LOG" 2>/dev/null || echo "No recent activity")
else
    FILE_EDITS=0
    TASKS_COMPLETED=0
    RECENT_CHANGES="No activity recorded"
fi

# Get git status
GIT_STATUS=$(git status --short 2>/dev/null | head -10 || echo "Not a git repository")
UNCOMMITTED_COUNT=$(git status --short 2>/dev/null | wc -l | tr -d ' ' || echo "0")

# Write session summary
cat > "$SUMMARY_FILE" << EOF
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

echo "Session summary saved to $SUMMARY_FILE"
