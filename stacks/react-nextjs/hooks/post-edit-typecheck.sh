#!/usr/bin/env bash
# post-edit-typecheck.sh
# Runs TypeScript type checking after files are edited by an agent.
#
# Usage: Called automatically by the agent framework after file edits.
# Expects file paths as arguments (used only to determine if typecheck is needed).
#
# Note: tsc --noEmit checks the entire project, not individual files.
# This is intentional -- a change in one file can cause type errors in others.

set -euo pipefail

SUPPORTED_EXTENSIONS="ts|tsx"

needs_typecheck=false

for file in "$@"; do
  if [[ -f "$file" ]]; then
    extension="${file##*.}"
    if [[ "$extension" =~ ^($SUPPORTED_EXTENSIONS)$ ]]; then
      needs_typecheck=true
      break
    fi
  fi
done

if [[ "$needs_typecheck" = false ]]; then
  exit 0
fi

# Check if TypeScript is available
if command -v npx &> /dev/null && [[ -f "node_modules/.bin/tsc" ]]; then
  echo "--- Running TypeScript type check ---"
  npx tsc --noEmit 2>&1 || {
    echo "--- Type errors found. Please fix before proceeding. ---"
    exit 1
  }
  echo "--- Type check passed ---"
elif [[ -f "tsconfig.json" ]]; then
  echo "--- TypeScript config found but tsc not installed. Run: npm install typescript ---"
  exit 1
else
  echo "--- No TypeScript config found. Skipping type check. ---"
fi
