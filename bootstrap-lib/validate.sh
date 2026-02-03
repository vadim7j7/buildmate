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
# validate_stack - Check that a single stack name is valid
# ---------------------------------------------------------------------------
validate_stack() {
    local stack="$1"

    for valid in ${VALID_STACKS_STR}; do
        if [[ "${stack}" == "${valid}" ]]; then
            return 0
        fi
    done

    return 1
}

# ---------------------------------------------------------------------------
# validate_stacks - Check that all stacks in a comma-separated list are valid
# ---------------------------------------------------------------------------
# Arguments:
#   $1 - stacks (comma-separated, e.g., "rails,react-native")
# ---------------------------------------------------------------------------
validate_stacks() {
    local stacks="$1"
    local stack_count=0

    # Replace commas with spaces for iteration
    local stacks_spaced="${stacks//,/ }"

    for stack in ${stacks_spaced}; do
        if ! validate_stack "${stack}"; then
            log_error "Invalid stack: '${stack}'"
            log_error "Valid stacks are: ${VALID_STACKS_STR}"
            exit 1
        fi
        stack_count=$((stack_count + 1))
    done

    if [[ ${stack_count} -eq 0 ]]; then
        log_error "No stacks specified"
        exit 1
    fi

    if [[ ${stack_count} -eq 1 ]]; then
        log_substep "Stack '${stacks}' is valid"
    else
        local stacks_display="${stacks//,/, }"
        log_substep "Stacks '${stacks_display}' are valid (${stack_count} stacks)"
    fi
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
