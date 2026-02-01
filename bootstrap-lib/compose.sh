#!/usr/bin/env bash
# =============================================================================
# compose.sh - Composition logic for layering shared + stack configs
# =============================================================================
# Sourced by bootstrap.sh. Provides the compose_agents function.
#
# Composition rules:
#   - shared/ is copied as the base layer
#   - stacks/<stack>/ is overlaid on top:
#       Agents:   stack-specific replace shared by name; stack-only added
#       Skills:   stack-specific replace shared by name; stack-only added
#       CLAUDE.md: shared + stack concatenated with separator
#       settings.json: deep-merged via jq (permission arrays concatenated)
#       Hooks:    stack-specific replace shared by name
#       Patterns: copied as-is from stack
#       Styles:   copied as-is from stack
#   - context/ and context/features/ directories are created
# =============================================================================

# ---------------------------------------------------------------------------
# compose_agents - Main composition entry point
# ---------------------------------------------------------------------------
# Arguments:
#   $1 - shared_dir   (e.g., /path/to/agents/shared)
#   $2 - stack_dir    (e.g., /path/to/agents/stacks/rails)
#   $3 - temp_dir     (output directory)
# ---------------------------------------------------------------------------
compose_agents() {
    local shared_dir="$1"
    local stack_dir="$2"
    local temp_dir="$3"

    log_substep "Using shared base: ${shared_dir}"
    log_substep "Using stack overlay: ${stack_dir}"

    # Step 1: Copy shared as base layer
    _compose_copy_shared "${shared_dir}" "${temp_dir}"

    # Step 1.5: Apply dependency stacks if a 'depends' file exists
    # This allows composite stacks (e.g., fullstack) to inherit from
    # multiple stacks (e.g., rails + react-nextjs) before applying
    # their own overlay.
    if [[ -f "${stack_dir}/depends" ]]; then
        log_substep "Stack has dependencies, applying dependency layers"
        while IFS= read -r dep_stack || [[ -n "${dep_stack}" ]]; do
            # Skip empty lines and comments
            dep_stack="$(echo "${dep_stack}" | sed 's/#.*//' | xargs)"
            if [[ -z "${dep_stack}" ]]; then
                continue
            fi
            local dep_dir="${STACKS_DIR}/${dep_stack}"
            if [[ ! -d "${dep_dir}" ]]; then
                log_warn "Dependency stack not found: ${dep_stack} (skipping)"
                continue
            fi
            log_substep "Applying dependency: ${dep_stack}"
            _compose_overlay_directory "agents" "${shared_dir}" "${dep_dir}" "${temp_dir}"
            _compose_overlay_directory "skills" "${shared_dir}" "${dep_dir}" "${temp_dir}"
            _compose_overlay_directory "hooks" "${shared_dir}" "${dep_dir}" "${temp_dir}"
            _compose_copy_stack_only "patterns" "${dep_dir}" "${temp_dir}"
            _compose_copy_stack_only "styles" "${dep_dir}" "${temp_dir}"

            # Copy stack-only top-level files (config.json, paths.json, etc.)
            # but NOT CLAUDE.md or settings.json (those are merged separately)
            for dep_file in "${dep_dir}"/*; do
                if [[ -f "${dep_file}" ]]; then
                    local fname
                    fname="$(basename "${dep_file}")"
                    case "${fname}" in
                        CLAUDE.md|settings.json|depends) ;; # Skip these
                        *) cp "${dep_file}" "${temp_dir}/${fname}" ;;
                    esac
                fi
            done
        done < "${stack_dir}/depends"
    fi

    # Step 2: Overlay stack-specific files (main stack wins over dependencies)
    _compose_overlay_directory "agents" "${shared_dir}" "${stack_dir}" "${temp_dir}"
    _compose_overlay_directory "skills" "${shared_dir}" "${stack_dir}" "${temp_dir}"
    _compose_overlay_directory "hooks" "${shared_dir}" "${stack_dir}" "${temp_dir}"

    # Step 3: Copy stack-only directories (patterns, styles)
    _compose_copy_stack_only "patterns" "${stack_dir}" "${temp_dir}"
    _compose_copy_stack_only "styles" "${stack_dir}" "${temp_dir}"

    # Step 4: Merge CLAUDE.md files
    _compose_claude_md "${shared_dir}" "${stack_dir}" "${temp_dir}"

    # Step 5: Merge settings.json files
    # For stacks with dependencies, we need to merge all settings.json files
    if [[ -f "${stack_dir}/depends" ]]; then
        _compose_settings_json_with_deps "${shared_dir}" "${stack_dir}" "${temp_dir}"
    else
        _compose_settings_json "${shared_dir}" "${stack_dir}" "${temp_dir}"
    fi

    # Step 6: Copy stack-specific top-level files (config.json, paths.json, etc.)
    for stack_file in "${stack_dir}"/*; do
        if [[ -f "${stack_file}" ]]; then
            local fname
            fname="$(basename "${stack_file}")"
            case "${fname}" in
                CLAUDE.md|settings.json|depends) ;; # Already handled
                *) cp "${stack_file}" "${temp_dir}/${fname}" ;;
            esac
        fi
    done

    # Step 7: Ensure context directories exist
    mkdir -p "${temp_dir}/context/features"

    log_substep "Composition complete"
}

# ---------------------------------------------------------------------------
# _compose_copy_shared - Copy the shared directory as the base layer
# ---------------------------------------------------------------------------
_compose_copy_shared() {
    local shared_dir="$1"
    local temp_dir="$2"

    log_substep "Copying shared base layer"

    # Copy all subdirectories from shared
    for item in "${shared_dir}"/*; do
        if [[ -d "${item}" ]]; then
            local dirname
            dirname="$(basename "${item}")"
            cp -R "${item}" "${temp_dir}/${dirname}"
        fi
    done

    # Copy top-level files from shared (CLAUDE.md, settings.json, etc.)
    for item in "${shared_dir}"/*; do
        if [[ -f "${item}" ]]; then
            cp "${item}" "${temp_dir}/"
        fi
    done
}

# ---------------------------------------------------------------------------
# _compose_overlay_directory - Overlay a stack directory on top of shared
# ---------------------------------------------------------------------------
# For agents/, skills/, hooks/: stack-specific items replace shared ones
# with the same name. Stack-only items are added.
# ---------------------------------------------------------------------------
_compose_overlay_directory() {
    local dir_name="$1"
    local shared_dir="$2"
    local stack_dir="$3"
    local temp_dir="$4"

    local stack_subdir="${stack_dir}/${dir_name}"

    # If the stack doesn't have this directory, nothing to overlay
    if [[ ! -d "${stack_subdir}" ]]; then
        return 0
    fi

    # Check if there's anything to overlay
    local has_content=false
    for item in "${stack_subdir}"/*; do
        if [[ -e "${item}" ]]; then
            has_content=true
            break
        fi
    done

    if [[ "${has_content}" == "false" ]]; then
        return 0
    fi

    log_substep "Overlaying stack ${dir_name}"

    # Ensure target directory exists
    mkdir -p "${temp_dir}/${dir_name}"

    # Copy/overlay each item from the stack directory
    for item in "${stack_subdir}"/*; do
        if [[ ! -e "${item}" ]]; then
            continue
        fi

        local item_name
        item_name="$(basename "${item}")"
        local target_item="${temp_dir}/${dir_name}/${item_name}"

        if [[ -d "${item}" ]]; then
            # Directory: replace entirely if it exists, or add if new
            if [[ -d "${target_item}" ]]; then
                rm -rf "${target_item}"
            fi
            cp -R "${item}" "${target_item}"
        elif [[ -f "${item}" ]]; then
            # File: replace if it exists, or add if new
            cp "${item}" "${target_item}"
        fi
    done
}

# ---------------------------------------------------------------------------
# _compose_copy_stack_only - Copy stack-only directories (no shared base)
# ---------------------------------------------------------------------------
_compose_copy_stack_only() {
    local dir_name="$1"
    local stack_dir="$2"
    local temp_dir="$3"

    local stack_subdir="${stack_dir}/${dir_name}"

    if [[ ! -d "${stack_subdir}" ]]; then
        return 0
    fi

    # Check if there's anything to copy
    local has_content=false
    for item in "${stack_subdir}"/*; do
        if [[ -e "${item}" ]]; then
            has_content=true
            break
        fi
    done

    if [[ "${has_content}" == "false" ]]; then
        return 0
    fi

    log_substep "Copying stack ${dir_name}"
    mkdir -p "${temp_dir}/${dir_name}"
    cp -R "${stack_subdir}"/* "${temp_dir}/${dir_name}/"
}

# ---------------------------------------------------------------------------
# _compose_claude_md - Concatenate shared + stack CLAUDE.md files
# ---------------------------------------------------------------------------
_compose_claude_md() {
    local shared_dir="$1"
    local stack_dir="$2"
    local temp_dir="$3"

    local shared_md="${shared_dir}/CLAUDE.md"
    local stack_md="${stack_dir}/CLAUDE.md"
    local output_md="${temp_dir}/CLAUDE.md"

    if [[ -f "${shared_md}" && -f "${stack_md}" ]]; then
        # Both exist: concatenate with separator
        log_substep "Merging CLAUDE.md (shared + stack)"
        cat "${shared_md}" > "${output_md}"
        echo "" >> "${output_md}"
        echo "---" >> "${output_md}"
        echo "" >> "${output_md}"
        echo "<!-- Stack-specific instructions -->" >> "${output_md}"
        echo "" >> "${output_md}"
        cat "${stack_md}" >> "${output_md}"
    elif [[ -f "${shared_md}" ]]; then
        # Only shared exists
        log_substep "Using shared CLAUDE.md"
        cp "${shared_md}" "${output_md}"
    elif [[ -f "${stack_md}" ]]; then
        # Only stack exists
        log_substep "Using stack CLAUDE.md"
        cp "${stack_md}" "${output_md}"
    else
        log_substep "No CLAUDE.md found in shared or stack (skipping)"
    fi
}

# ---------------------------------------------------------------------------
# _compose_settings_json - Deep-merge settings.json files
# ---------------------------------------------------------------------------
# Uses jq for deep merging. Permission arrays are concatenated and
# deduplicated. Other fields are recursively merged (stack wins on conflict).
# ---------------------------------------------------------------------------
_compose_settings_json() {
    local shared_dir="$1"
    local stack_dir="$2"
    local temp_dir="$3"

    local shared_json="${shared_dir}/settings.json"
    local stack_json="${stack_dir}/settings.json"
    local output_json="${temp_dir}/settings.json"

    if [[ -f "${shared_json}" && -f "${stack_json}" ]]; then
        log_substep "Deep-merging settings.json"

        # Check if jq is available
        if command -v jq &>/dev/null; then
            # Deep merge with special handling for permission arrays
            jq -s '
                def deep_merge(a; b):
                    a as $a | b as $b |
                    if ($a | type) == "object" and ($b | type) == "object" then
                        ($a | keys_unsorted) + ($b | keys_unsorted) | unique |
                        map(. as $key |
                            if ($a | has($key)) and ($b | has($key)) then
                                if (($a[$key] | type) == "array") and (($b[$key] | type) == "array") then
                                    { ($key): (($a[$key] + $b[$key]) | unique) }
                                elif (($a[$key] | type) == "object") and (($b[$key] | type) == "object") then
                                    { ($key): deep_merge($a[$key]; $b[$key]) }
                                else
                                    { ($key): $b[$key] }
                                end
                            elif ($a | has($key)) then
                                { ($key): $a[$key] }
                            else
                                { ($key): $b[$key] }
                            end
                        ) | add // {}
                    elif ($b | type) == "null" then $a
                    else $b
                    end;
                deep_merge(.[0]; .[1])
            ' "${shared_json}" "${stack_json}" > "${output_json}"
        else
            # Fallback: stack settings take precedence
            log_warn "jq not found. Using stack settings.json as-is (no merge)."
            cp "${stack_json}" "${output_json}"
        fi
    elif [[ -f "${shared_json}" ]]; then
        log_substep "Using shared settings.json"
        cp "${shared_json}" "${output_json}"
    elif [[ -f "${stack_json}" ]]; then
        log_substep "Using stack settings.json"
        cp "${stack_json}" "${output_json}"
    fi
}

# ---------------------------------------------------------------------------
# _compose_settings_json_with_deps - Merge settings across shared + deps + stack
# ---------------------------------------------------------------------------
# For composite stacks (with depends file), progressively merges:
#   shared → dep1 → dep2 → ... → stack
# ---------------------------------------------------------------------------
_compose_settings_json_with_deps() {
    local shared_dir="$1"
    local stack_dir="$2"
    local temp_dir="$3"

    local shared_json="${shared_dir}/settings.json"
    local stack_json="${stack_dir}/settings.json"
    local output_json="${temp_dir}/settings.json"

    if ! command -v jq &>/dev/null; then
        log_warn "jq not found. Using stack settings.json as-is (no merge)."
        if [[ -f "${stack_json}" ]]; then
            cp "${stack_json}" "${output_json}"
        elif [[ -f "${shared_json}" ]]; then
            cp "${shared_json}" "${output_json}"
        fi
        return 0
    fi

    # Start with shared settings
    local current_json=""
    if [[ -f "${shared_json}" ]]; then
        current_json="${shared_json}"
    fi

    # Progressively merge each dependency's settings
    while IFS= read -r dep_stack || [[ -n "${dep_stack}" ]]; do
        dep_stack="$(echo "${dep_stack}" | sed 's/#.*//' | xargs)"
        if [[ -z "${dep_stack}" ]]; then
            continue
        fi
        local dep_json="${STACKS_DIR}/${dep_stack}/settings.json"
        if [[ -f "${dep_json}" && -n "${current_json}" ]]; then
            log_substep "Merging settings from dependency: ${dep_stack}"
            local merged
            merged="$(jq -s '
                def deep_merge(a; b):
                    a as $a | b as $b |
                    if ($a | type) == "object" and ($b | type) == "object" then
                        ($a | keys_unsorted) + ($b | keys_unsorted) | unique |
                        map(. as $key |
                            if ($a | has($key)) and ($b | has($key)) then
                                if (($a[$key] | type) == "array") and (($b[$key] | type) == "array") then
                                    { ($key): (($a[$key] + $b[$key]) | unique) }
                                elif (($a[$key] | type) == "object") and (($b[$key] | type) == "object") then
                                    { ($key): deep_merge($a[$key]; $b[$key]) }
                                else
                                    { ($key): $b[$key] }
                                end
                            elif ($a | has($key)) then
                                { ($key): $a[$key] }
                            else
                                { ($key): $b[$key] }
                            end
                        ) | add // {}
                    elif ($b | type) == "null" then $a
                    else $b
                    end;
                deep_merge(.[0]; .[1])
            ' "${current_json}" "${dep_json}")"
            # Write to a temp file for the next iteration
            local merge_tmp="${temp_dir}/.settings_merge_tmp.json"
            echo "${merged}" > "${merge_tmp}"
            current_json="${merge_tmp}"
        elif [[ -f "${dep_json}" ]]; then
            current_json="${dep_json}"
        fi
    done < "${stack_dir}/depends"

    # Finally merge with the main stack's settings
    if [[ -f "${stack_json}" && -n "${current_json}" ]]; then
        log_substep "Merging settings from main stack"
        jq -s '
            def deep_merge(a; b):
                a as $a | b as $b |
                if ($a | type) == "object" and ($b | type) == "object" then
                    ($a | keys_unsorted) + ($b | keys_unsorted) | unique |
                    map(. as $key |
                        if ($a | has($key)) and ($b | has($key)) then
                            if (($a[$key] | type) == "array") and (($b[$key] | type) == "array") then
                                { ($key): (($a[$key] + $b[$key]) | unique) }
                            elif (($a[$key] | type) == "object") and (($b[$key] | type) == "object") then
                                { ($key): deep_merge($a[$key]; $b[$key]) }
                            else
                                { ($key): $b[$key] }
                            end
                        elif ($a | has($key)) then
                            { ($key): $a[$key] }
                        else
                            { ($key): $b[$key] }
                        end
                    ) | add // {}
                elif ($b | type) == "null" then $a
                else $b
                end;
            deep_merge(.[0]; .[1])
        ' "${current_json}" "${stack_json}" > "${output_json}"
    elif [[ -n "${current_json}" ]]; then
        cp "${current_json}" "${output_json}"
    elif [[ -f "${stack_json}" ]]; then
        cp "${stack_json}" "${output_json}"
    fi

    # Clean up temp merge file
    rm -f "${temp_dir}/.settings_merge_tmp.json"
}
