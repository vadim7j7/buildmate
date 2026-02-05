#!/bin/bash
# Session Save Hook
# Automatically saves active work context when a session ends.
# This file is read by /recap to restore context in the next session.

set -e

CONTEXT_DIR=".claude/context"
ACTIVE_WORK_FILE="$CONTEXT_DIR/active-work.md"

# Ensure context directory exists
mkdir -p "$CONTEXT_DIR"

# Get current timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Get current branch
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")

# Get uncommitted changes summary
CHANGES=$(git status --short 2>/dev/null | head -10)
CHANGE_COUNT=$(git status --short 2>/dev/null | wc -l | tr -d ' ')

# Get recent commits on this branch
RECENT_COMMITS=$(git log --oneline -5 2>/dev/null || echo "No commits")

# Get in-progress features
IN_PROGRESS=""
if [ -d "$CONTEXT_DIR/features" ]; then
    for f in "$CONTEXT_DIR/features"/*.md; do
        if [ -f "$f" ]; then
            if grep -q "status:.*in-progress\|status:.*testing\|status:.*review" "$f" 2>/dev/null; then
                TITLE=$(grep -m1 "^# " "$f" | sed 's/^# //')
                STATUS=$(grep -m1 "status:" "$f" | sed 's/.*status: *//')
                IN_PROGRESS="$IN_PROGRESS\n- $TITLE ($STATUS)"
            fi
        fi
    done
fi

# Write active work file
cat > "$ACTIVE_WORK_FILE" << EOF
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

echo "Session context saved to $ACTIVE_WORK_FILE"
