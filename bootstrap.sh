#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Agents Template Generator - Bootstrap Script
# =============================================================================
# Usage: ./bootstrap.sh <stack> <target-path> [--force]
#
# Bootstraps a .claude/ agent configuration into the target project by
# composing shared infrastructure with stack-specific overlays.
#
# Available stacks: rails, react-nextjs, react-native, fullstack
# =============================================================================

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LIB_DIR="${SCRIPT_DIR}/bootstrap-lib"
readonly SHARED_DIR="${SCRIPT_DIR}/shared"
readonly STACKS_DIR="${SCRIPT_DIR}/stacks"
readonly VERSION="1.0.0"

# ---------------------------------------------------------------------------
# Colors and formatting
# ---------------------------------------------------------------------------
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly MAGENTA='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly DIM='\033[2m'
readonly NC='\033[0m' # No Color

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_step() {
    echo -e "\n${MAGENTA}${BOLD}==> $*${NC}"
}

log_substep() {
    echo -e "  ${CYAN}->$NC $*"
}

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------
usage() {
    cat <<EOF
${BOLD}Agents Template Generator v${VERSION}${NC}

${BOLD}Usage:${NC}
    ./bootstrap.sh <stack> <target-path> [--force]

${BOLD}Available stacks:${NC}
    rails          Ruby on Rails applications
    react-nextjs   React + Next.js applications
    react-native   React Native mobile applications
    fullstack      Combined Rails API + React frontend

${BOLD}Options:${NC}
    --force        Overwrite existing .claude/ directory in target
    --help, -h     Show this help message

${BOLD}Examples:${NC}
    ./bootstrap.sh rails /path/to/my-rails-app
    ./bootstrap.sh react-nextjs /path/to/my-react-app --force
    ./bootstrap.sh fullstack ~/projects/my-app

${BOLD}What it does:${NC}
    1. Validates inputs and target project
    2. Composes shared + stack-specific agent configs
    3. Installs composed configs into target/.claude/
    4. Runs post-install setup (permissions, gitignore, etc.)
EOF
}

# ---------------------------------------------------------------------------
# Cleanup handler
# ---------------------------------------------------------------------------
TEMP_DIR=""

cleanup() {
    if [[ -n "${TEMP_DIR}" && -d "${TEMP_DIR}" ]]; then
        rm -rf "${TEMP_DIR}"
    fi
}

trap cleanup EXIT

# ---------------------------------------------------------------------------
# Source library scripts
# ---------------------------------------------------------------------------
source_lib() {
    local lib_file="${LIB_DIR}/$1"
    if [[ ! -f "${lib_file}" ]]; then
        log_error "Missing library script: ${lib_file}"
        log_error "The bootstrap-lib/ directory may be incomplete."
        exit 1
    fi
    # shellcheck source=/dev/null
    source "${lib_file}"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    # Handle --help anywhere in args
    for arg in "$@"; do
        if [[ "${arg}" == "--help" || "${arg}" == "-h" ]]; then
            usage
            exit 0
        fi
    done

    # Parse arguments
    local stack=""
    local target_path=""
    local force=false

    for arg in "$@"; do
        case "${arg}" in
            --force)
                force=true
                ;;
            -*)
                log_error "Unknown option: ${arg}"
                echo ""
                usage
                exit 1
                ;;
            *)
                if [[ -z "${stack}" ]]; then
                    stack="${arg}"
                elif [[ -z "${target_path}" ]]; then
                    target_path="${arg}"
                else
                    log_error "Unexpected argument: ${arg}"
                    echo ""
                    usage
                    exit 1
                fi
                ;;
        esac
    done

    # Check required arguments
    if [[ -z "${stack}" || -z "${target_path}" ]]; then
        log_error "Missing required arguments."
        echo ""
        usage
        exit 1
    fi

    # Resolve target path to absolute
    target_path="$(cd "${target_path}" 2>/dev/null && pwd || echo "${target_path}")"

    # Print banner
    echo ""
    echo -e "${BOLD}${MAGENTA}  Agents Template Generator v${VERSION}${NC}"
    echo -e "${DIM}  Bootstrapping ${CYAN}${stack}${DIM} stack into ${CYAN}${target_path}${NC}"
    echo ""

    # Source library scripts
    source_lib "validate.sh"
    source_lib "compose.sh"
    source_lib "install.sh"
    source_lib "post-install.sh"

    # Export variables for library scripts
    export STACK="${stack}"
    export TARGET_PATH="${target_path}"
    export FORCE="${force}"
    export SCRIPT_DIR
    export SHARED_DIR
    export STACKS_DIR

    # Phase 1: Validate
    log_step "Phase 1/4: Validating inputs"
    validate_stack "${stack}"
    validate_target "${target_path}"
    validate_git_repo "${target_path}"
    validate_no_existing_claude "${target_path}" "${force}"
    log_success "Validation passed"

    # Phase 2: Compose
    log_step "Phase 2/4: Composing configuration"
    TEMP_DIR="$(mktemp -d)"
    export TEMP_DIR
    compose_agents "${SHARED_DIR}" "${STACKS_DIR}/${stack}" "${TEMP_DIR}"
    log_success "Configuration composed in temp directory"

    # Phase 3: Install
    log_step "Phase 3/4: Installing to target"
    install_to_target "${TEMP_DIR}" "${target_path}" "${force}"
    log_success "Configuration installed"

    # Phase 4: Post-install
    log_step "Phase 4/4: Running post-install tasks"
    post_install "${target_path}" "${stack}"
    log_success "Post-install complete"

    # Done
    echo ""
    echo -e "${GREEN}${BOLD}  Bootstrap complete!${NC}"
    echo ""
}

main "$@"
