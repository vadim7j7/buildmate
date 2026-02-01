#!/usr/bin/env bash
# post-edit-typecheck.sh
# Runs TypeScript type checking after file edits.
# Uses tsc --noEmit to check for type errors without producing output files.
#
# Usage: post-edit-typecheck.sh [file1] [file2] ...
# Note: TypeScript always checks the full project (tsconfig.json scope).
#       File arguments are accepted but tsc --noEmit runs project-wide.
# Exit codes: 0 = no errors, 1 = tsc not found, 2 = type errors found

set -euo pipefail

# Check that npx is available
if ! command -v npx &>/dev/null; then
  echo "[post-edit-typecheck] npx not found, skipping type check."
  exit 1
fi

# Check that tsconfig.json exists
if [ ! -f "tsconfig.json" ]; then
  echo "[post-edit-typecheck] No tsconfig.json found, skipping type check."
  exit 0
fi

# Check if any of the provided files are TypeScript files
HAS_TS_FILES=false
if [ $# -gt 0 ]; then
  for file in "$@"; do
    case "$file" in
      *.ts|*.tsx)
        HAS_TS_FILES=true
        break
        ;;
    esac
  done
else
  # No files provided, run anyway (might be called without args)
  HAS_TS_FILES=true
fi

if [ "$HAS_TS_FILES" = false ]; then
  echo "[post-edit-typecheck] No TypeScript files edited, skipping."
  exit 0
fi

echo "[post-edit-typecheck] Running TypeScript type check..."

# Run tsc --noEmit for the full project
# TypeScript needs to check the full project graph for accurate results
if npx tsc --noEmit 2>&1; then
  echo "[post-edit-typecheck] No type errors found."
else
  TSC_EXIT=$?
  echo "[post-edit-typecheck] TypeScript found errors (exit code: $TSC_EXIT)."
  echo "[post-edit-typecheck] Run 'npx tsc --noEmit' to see full output."
  exit 2
fi
