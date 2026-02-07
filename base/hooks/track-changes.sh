#!/bin/bash
# Track Changes Hook (PostToolUse: Edit, Write, NotebookEdit)
# Logs file modifications made during agent work sessions.
# Creates an audit trail of what files were changed and when.
#
# Input: JSON via stdin with tool_name, tool_input, tool_response
# Output: Appends to .claude/context/agent-activity.log

# Don't use set -e - we want to be non-blocking
# Hooks should not fail the main operation

CONTEXT_DIR=".claude/context"
ACTIVITY_LOG="$CONTEXT_DIR/agent-activity.log"

# Check if jq is available
if ! command -v jq &> /dev/null; then
    exit 0  # Silently skip if jq not installed
fi

# Read JSON input from stdin
INPUT=$(cat 2>/dev/null) || exit 0

# Extract tool info (silently fail if jq errors)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null) || exit 0
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null) || exit 0
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null) || TIMESTAMP="unknown"

# Only proceed if we have a file path
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Ensure context directory exists
mkdir -p "$CONTEXT_DIR" 2>/dev/null || exit 0

# Log the change
echo "[$TIMESTAMP] $TOOL_NAME: $FILE_PATH" >> "$ACTIVITY_LOG" 2>/dev/null

exit 0
