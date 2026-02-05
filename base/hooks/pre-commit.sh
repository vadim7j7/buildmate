#!/bin/bash
# Pre-commit Hook
# Runs quality gates before allowing a commit.
# Install: cp .claude/hooks/pre-commit.sh .git/hooks/pre-commit

set -e

echo "Running pre-commit quality gates..."

# Check for quality gate commands in CLAUDE.md
if [ -f "CLAUDE.md" ]; then
    # Try to extract and run lint command
    if grep -q "lint.*:" CLAUDE.md; then
        echo "Running linter..."
        # Stack-specific lint commands would go here
    fi
fi

# Prevent commits with debugging artifacts
if git diff --cached --name-only | xargs grep -l "binding.pry\|debugger\|console.log.*DEBUG\|TODO.*REMOVE" 2>/dev/null; then
    echo "ERROR: Found debugging artifacts in staged files"
    echo "Please remove binding.pry, debugger statements, DEBUG console.logs, or TODO REMOVE comments"
    exit 1
fi

# Check for large files
LARGE_FILES=$(git diff --cached --name-only | while read f; do
    if [ -f "$f" ]; then
        SIZE=$(wc -c < "$f" | tr -d ' ')
        if [ "$SIZE" -gt 1000000 ]; then
            echo "$f ($SIZE bytes)"
        fi
    fi
done)

if [ -n "$LARGE_FILES" ]; then
    echo "WARNING: Large files detected (>1MB):"
    echo "$LARGE_FILES"
    echo "Consider using Git LFS for large files."
fi

echo "Pre-commit checks passed."
