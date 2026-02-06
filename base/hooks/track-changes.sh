#!/bin/bash
# Track Changes Hook (PostToolUse: Edit, Write, NotebookEdit)
# Logs file modifications made during agent work sessions.
# Creates an audit trail of what files were changed and when.
#
# Input: JSON via stdin with tool_name, tool_input, tool_response
# Output: Appends to .claude/context/agent-activity.log

set -e

CONTEXT_DIR=".claude/context"
ACTIVITY_LOG="$CONTEXT_DIR/agent-activity.log"

# Read JSON input from stdin
INPUT=$(cat)

# Extract tool info
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Only proceed if we have a file path
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Ensure context directory exists
mkdir -p "$CONTEXT_DIR"

# Log the change
echo "[$TIMESTAMP] $TOOL_NAME: $FILE_PATH" >> "$ACTIVITY_LOG"
