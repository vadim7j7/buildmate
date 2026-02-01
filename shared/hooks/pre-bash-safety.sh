#!/usr/bin/env bash
# pre-bash-safety.sh -- Safety hook that blocks dangerous bash commands.
#
# This hook is invoked before any bash command is executed by an agent.
# It inspects the command string and blocks known-dangerous patterns.
#
# Exit codes:
#   0  Command is allowed
#   2  Command is blocked (dangerous)
#
# Usage:
#   echo "rm -rf /" | ./pre-bash-safety.sh
#   ./pre-bash-safety.sh "git push --force origin main"

set -euo pipefail

# ---------------------------------------------------------------------------
# Read the command
# ---------------------------------------------------------------------------

# Accept command as argument or from stdin
if [[ $# -gt 0 ]]; then
  COMMAND="$*"
else
  COMMAND="$(cat)"
fi

# Normalise: collapse whitespace, lowercase for pattern matching
NORMALISED="$(echo "${COMMAND}" | tr '[:upper:]' '[:lower:]' | tr -s '[:space:]' ' ')"

# ---------------------------------------------------------------------------
# Blocked patterns
# ---------------------------------------------------------------------------

block() {
  echo "BLOCKED: $1" >&2
  echo "Command: ${COMMAND}" >&2
  exit 2
}

# --- Destructive filesystem commands ---

# Block: rm -rf / (root deletion)
if echo "${NORMALISED}" | grep -qE 'rm\s+(-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*)\s+/\s*$'; then
  block "rm -rf / -- Refusing to delete the entire filesystem."
fi

# Block: rm -rf /* (root contents deletion)
if echo "${NORMALISED}" | grep -qE 'rm\s+(-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*)\s+/\*'; then
  block "rm -rf /* -- Refusing to delete all files in the root filesystem."
fi

# Block: rm -rf ~ (home directory deletion)
if echo "${NORMALISED}" | grep -qE 'rm\s+(-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*)\s+~\s*$'; then
  block "rm -rf ~ -- Refusing to delete the home directory."
fi

# Block: rm -rf ~/* (home contents deletion)
if echo "${NORMALISED}" | grep -qE 'rm\s+(-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*)\s+~/\*'; then
  block "rm -rf ~/* -- Refusing to delete all files in the home directory."
fi

# --- Destructive git commands on protected branches ---

# Block: git push --force to main or master
if echo "${NORMALISED}" | grep -qE 'git\s+push\s+.*--force.*\s+(origin\s+)?(main|master)'; then
  block "git push --force to main/master -- Refusing to force-push to a protected branch."
fi

if echo "${NORMALISED}" | grep -qE 'git\s+push\s+.*-f\s+.*\s+(origin\s+)?(main|master)'; then
  block "git push -f to main/master -- Refusing to force-push to a protected branch."
fi

# Block: git push --force-with-lease to main or master
if echo "${NORMALISED}" | grep -qE 'git\s+push\s+.*--force-with-lease.*\s+(origin\s+)?(main|master)'; then
  block "git push --force-with-lease to main/master -- Refusing to force-push to a protected branch."
fi

# Block: git reset --hard (without explicit user request, the agent should not do this)
if echo "${NORMALISED}" | grep -qE 'git\s+reset\s+--hard'; then
  block "git reset --hard -- Refusing to discard all uncommitted changes."
fi

# Block: git clean -fd (removes untracked files and directories)
if echo "${NORMALISED}" | grep -qE 'git\s+clean\s+(-[a-z]*f[a-z]*d|-[a-z]*d[a-z]*f)'; then
  block "git clean -fd -- Refusing to remove untracked files and directories."
fi

# Block: git clean -f (removes untracked files)
if echo "${NORMALISED}" | grep -qE 'git\s+clean\s+-[a-z]*f'; then
  block "git clean -f -- Refusing to remove untracked files."
fi

# Block: git checkout . (discard all working tree changes)
if echo "${NORMALISED}" | grep -qE 'git\s+checkout\s+\.\s*$'; then
  block "git checkout . -- Refusing to discard all working tree changes."
fi

# Block: git restore . (discard all working tree changes)
if echo "${NORMALISED}" | grep -qE 'git\s+restore\s+\.\s*$'; then
  block "git restore . -- Refusing to discard all working tree changes."
fi

# --- Other dangerous patterns ---

# Block: dd writing to block devices
if echo "${NORMALISED}" | grep -qE 'dd\s+.*of=/dev/'; then
  block "dd to block device -- Refusing to write directly to a device."
fi

# Block: mkfs on any device
if echo "${NORMALISED}" | grep -qE 'mkfs'; then
  block "mkfs -- Refusing to format a filesystem."
fi

# Block: chmod 777 recursively (overly permissive)
if echo "${NORMALISED}" | grep -qE 'chmod\s+(-[a-z]*r[a-z]*\s+)?777\s+/'; then
  block "chmod -R 777 / -- Refusing to make system files world-writable."
fi

# ---------------------------------------------------------------------------
# Command is allowed
# ---------------------------------------------------------------------------

exit 0
