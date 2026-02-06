#!/bin/bash
# Task Complete Hook (PostToolUse: Task)
# Logs when a Task (subagent) completes and captures its result summary.
#
# Input: JSON via stdin with tool_name, tool_input, tool_response
# Output: Appends to .claude/context/agent-activity.log

set -e

CONTEXT_DIR=".claude/context"
ACTIVITY_LOG="$CONTEXT_DIR/agent-activity.log"

# Read JSON input from stdin
INPUT=$(cat)

# Extract task info
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
DESCRIPTION=$(echo "$INPUT" | jq -r '.tool_input.description // "unknown task"')
SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // "general-purpose"')
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Only log Task tool completions
if [ "$TOOL_NAME" != "Task" ]; then
    exit 0
fi

# Ensure context directory exists
mkdir -p "$CONTEXT_DIR"

# Log the task completion
echo "[$TIMESTAMP] Task completed: $DESCRIPTION (agent: $SUBAGENT_TYPE)" >> "$ACTIVITY_LOG"
