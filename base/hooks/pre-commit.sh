#!/bin/bash
# Pre-commit Hook
# Blocks commits with debugging artifacts and warns about large files.
# Quality gates are run by the /ship skill and the grind agent.
# Install: cp .claude/hooks/pre-commit.sh .git/hooks/pre-commit

set -e

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
    # Fallback to current directory (git hooks run from repo root anyway)
    echo "$PWD"
}

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(find_project_root)}"
cd "$PROJECT_ROOT"

echo "Running pre-commit quality gates..."

# Prevent commits with debugging artifacts
if git diff --cached --name-only --diff-filter=ACM | grep -v "^\.claude/" | xargs grep -l "binding.pry\|debugger\|console.log.*DEBUG\|TODO.*REMOVE" 2>/dev/null; then
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
