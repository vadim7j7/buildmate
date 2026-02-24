#!/bin/bash
# Session Save Hook
# Automatically saves active work context when a session ends.
# This file is read by /recap to restore context in the next session.

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

PROJECT_ROOT=$(find_project_root)
CONTEXT_DIR="$PROJECT_ROOT/.claude/context"
ACTIVE_WORK_FILE="$CONTEXT_DIR/active-work.md"

# Ensure context directory exists
mkdir -p "$CONTEXT_DIR" 2>/dev/null || exit 0

# Get current timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null) || TIMESTAMP="unknown"

# Get current branch
BRANCH=$(git -C "$PROJECT_ROOT" branch --show-current 2>/dev/null || echo "unknown")

# Get uncommitted changes summary
CHANGES=$(git -C "$PROJECT_ROOT" status --short 2>/dev/null | head -10)
CHANGE_COUNT=$(git -C "$PROJECT_ROOT" status --short 2>/dev/null | wc -l | tr -d ' ')

# Get recent commits on this branch
RECENT_COMMITS=$(git -C "$PROJECT_ROOT" log --oneline -5 2>/dev/null || echo "No commits")

# Get in-progress features
IN_PROGRESS=""
if [ -d "$CONTEXT_DIR/features" ]; then
    for f in "$CONTEXT_DIR/features"/*.md; do
        if [ -f "$f" ]; then
            if grep -qi "status:.*in.progress\|status:.*testing\|status:.*review" "$f" 2>/dev/null; then
                TITLE=$(grep -m1 "^# " "$f" 2>/dev/null | sed 's/^# //')
                STATUS=$(grep -m1 -i "status:" "$f" 2>/dev/null | sed 's/.*[Ss]tatus: *//')
                IN_PROGRESS="$IN_PROGRESS\n- $TITLE ($STATUS)"
            fi
        fi
    done
fi

# Write active work file
cat > "$ACTIVE_WORK_FILE" 2>/dev/null << EOF
# Active Work Context

**Saved:** $TIMESTAMP
**Branch:** \`$BRANCH\`

## Current State

- **Uncommitted changes:** $CHANGE_COUNT files
- **Working on:** $BRANCH

## Recent Commits

\`\`\`
$RECENT_COMMITS
\`\`\`

## In-Progress Features
$(echo -e "$IN_PROGRESS" | grep -v "^$" || echo "None")

## Uncommitted Changes

\`\`\`
$CHANGES
\`\`\`
EOF

exit 0
