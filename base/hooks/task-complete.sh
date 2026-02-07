#!/bin/bash
# Task Complete Hook (PostToolUse: Task)
# Logs when a Task (subagent) completes and captures its result summary.
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

# Extract task info (silently fail if jq errors)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null) || exit 0
DESCRIPTION=$(echo "$INPUT" | jq -r '.tool_input.description // "unknown task"' 2>/dev/null) || DESCRIPTION="unknown task"
SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // "general-purpose"' 2>/dev/null) || SUBAGENT_TYPE="general-purpose"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null) || TIMESTAMP="unknown"

# Only log Task tool completions
if [ "$TOOL_NAME" != "Task" ]; then
    exit 0
fi

# Ensure context directory exists
mkdir -p "$CONTEXT_DIR" 2>/dev/null || exit 0

# Log the task completion
echo "[$TIMESTAMP] Task completed: $DESCRIPTION (agent: $SUBAGENT_TYPE)" >> "$ACTIVITY_LOG" 2>/dev/null

exit 0
