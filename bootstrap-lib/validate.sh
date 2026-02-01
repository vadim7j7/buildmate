#!/usr/bin/env bash
# =============================================================================
# validate.sh - Input validation for the bootstrap script
# =============================================================================
# Sourced by bootstrap.sh. Provides validation functions.
# =============================================================================

# ---------------------------------------------------------------------------
# Valid stacks (space-separated string for bash 3.2 compatibility with set -u)
# ---------------------------------------------------------------------------
readonly VALID_STACKS_STR="rails react-nextjs react-native fullstack python-fastapi"

# ---------------------------------------------------------------------------
# validate_stack - Check that the stack name is valid
# ---------------------------------------------------------------------------
validate_stack() {
    local stack="$1"

    for valid in ${VALID_STACKS_STR}; do
        if [[ "${stack}" == "${valid}" ]]; then
            log_substep "Stack '${stack}' is valid"
            return 0
        fi
    done

    log_error "Invalid stack: '${stack}'"
    log_error "Valid stacks are: ${VALID_STACKS_STR}"
    exit 1
}

# ---------------------------------------------------------------------------
# validate_target - Check that the target path exists and is a directory
# ---------------------------------------------------------------------------
validate_target() {
    local target="$1"

    if [[ ! -e "${target}" ]]; then
        log_error "Target path does not exist: ${target}"
        exit 1
    fi

    if [[ ! -d "${target}" ]]; then
        log_error "Target path is not a directory: ${target}"
        exit 1
    fi

    if [[ ! -w "${target}" ]]; then
        log_error "Target path is not writable: ${target}"
        exit 1
    fi

    log_substep "Target path exists and is writable"
}

# ---------------------------------------------------------------------------
# validate_git_repo - Warn if the target is not a git repository
# ---------------------------------------------------------------------------
validate_git_repo() {
    local target="$1"

    if [[ ! -d "${target}/.git" ]]; then
        log_warn "Target is not a git repository. Some features (hooks, gitignore updates) may not work as expected."
        log_warn "Consider running 'git init' in the target directory first."
    else
        log_substep "Target is a git repository"
    fi
}

# ---------------------------------------------------------------------------
# validate_no_existing_claude - Check for existing .claude/ directory
# ---------------------------------------------------------------------------
validate_no_existing_claude() {
    local target="$1"
    local force="$2"

    if [[ -d "${target}/.claude" ]]; then
        if [[ "${force}" == "true" ]]; then
            log_warn "Existing .claude/ directory found. Will overwrite (--force)."
        else
            log_error "Target already has a .claude/ directory: ${target}/.claude"
            log_error "Use --force to overwrite existing configuration."
            exit 1
        fi
    else
        log_substep "No existing .claude/ directory"
    fi
}
