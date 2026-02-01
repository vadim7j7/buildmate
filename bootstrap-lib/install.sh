#!/usr/bin/env bash
# =============================================================================
# install.sh - Copy composed output to the target project
# =============================================================================
# Sourced by bootstrap.sh. Provides the install_to_target function.
# =============================================================================

# ---------------------------------------------------------------------------
# install_to_target - Copy composed configuration to the target project
# ---------------------------------------------------------------------------
# Arguments:
#   $1 - temp_dir     (composed output directory)
#   $2 - target_path  (target project root)
#   $3 - force        ("true" or "false")
# ---------------------------------------------------------------------------
install_to_target() {
    local temp_dir="$1"
    local target_path="$2"
    local force="$3"

    # Handle existing .claude/ directory
    if [[ -d "${target_path}/.claude" ]]; then
        if [[ "${force}" == "true" ]]; then
            log_substep "Removing existing .claude/ directory"
            rm -rf "${target_path}/.claude"
        else
            log_error "Target already has .claude/ directory. This should have been caught by validation."
            exit 1
        fi
    fi

    # Create .claude/ directory
    mkdir -p "${target_path}/.claude"

    # Copy all composed content into .claude/ (except CLAUDE.md which goes to root)
    log_substep "Copying agent configuration to .claude/"
    _install_claude_directory "${temp_dir}" "${target_path}"

    # Handle CLAUDE.md (goes to project root, not inside .claude/)
    _install_claude_md "${temp_dir}" "${target_path}" "${force}"

    # Create settings.local.json if it doesn't exist
    _install_settings_local "${target_path}"
}

# ---------------------------------------------------------------------------
# _install_claude_directory - Copy composed files into target/.claude/
# ---------------------------------------------------------------------------
_install_claude_directory() {
    local temp_dir="$1"
    local target_path="$2"

    local claude_dir="${target_path}/.claude"

    for item in "${temp_dir}"/*; do
        if [[ ! -e "${item}" ]]; then
            continue
        fi

        local item_name
        item_name="$(basename "${item}")"

        # CLAUDE.md is handled separately (goes to project root)
        if [[ "${item_name}" == "CLAUDE.md" ]]; then
            continue
        fi

        if [[ -d "${item}" ]]; then
            cp -R "${item}" "${claude_dir}/${item_name}"
            log_substep "Installed ${item_name}/"
        elif [[ -f "${item}" ]]; then
            cp "${item}" "${claude_dir}/${item_name}"
            log_substep "Installed ${item_name}"
        fi
    done
}

# ---------------------------------------------------------------------------
# _install_claude_md - Install CLAUDE.md to project root
# ---------------------------------------------------------------------------
_install_claude_md() {
    local temp_dir="$1"
    local target_path="$2"
    local force="$3"

    local composed_md="${temp_dir}/CLAUDE.md"
    local target_md="${target_path}/CLAUDE.md"

    if [[ ! -f "${composed_md}" ]]; then
        log_substep "No CLAUDE.md to install (skipping)"
        return 0
    fi

    if [[ -f "${target_md}" ]]; then
        if [[ "${force}" == "true" ]]; then
            log_substep "Overwriting existing CLAUDE.md"
            cp "${composed_md}" "${target_md}"
        else
            # Append to existing CLAUDE.md
            log_substep "Appending agent instructions to existing CLAUDE.md"
            echo "" >> "${target_md}"
            echo "---" >> "${target_md}"
            echo "" >> "${target_md}"
            echo "<!-- Agent configuration (added by agents template generator) -->" >> "${target_md}"
            echo "" >> "${target_md}"
            cat "${composed_md}" >> "${target_md}"
        fi
    else
        log_substep "Installing CLAUDE.md to project root"
        cp "${composed_md}" "${target_md}"
    fi
}

# ---------------------------------------------------------------------------
# _install_settings_local - Create settings.local.json from template
# ---------------------------------------------------------------------------
_install_settings_local() {
    local target_path="$1"

    local settings_local="${target_path}/.claude/settings.local.json"

    if [[ -f "${settings_local}" ]]; then
        log_substep "settings.local.json already exists (skipping)"
        return 0
    fi

    log_substep "Creating settings.local.json template"

    # Create a minimal settings.local.json template
    cat > "${settings_local}" <<'SETTINGS_LOCAL'
{
  "permissions": {
    "allow": [],
    "deny": []
  },
  "env": {}
}
SETTINGS_LOCAL
}
